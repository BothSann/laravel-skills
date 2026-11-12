<?php

declare(strict_types=1);

/**
 * Helpers for the laravel-learn skill. Read-only except `cleanup`.
 *
 *   php learn.php scan <repo> [--no-gh]          project facts, lessons, and blockers
 *   php learn.php step <GUIDE.md> <number>       print one step of a guide
 *   php learn.php guide-size <GUIDE.md>          fail when a guide is over its limits
 *   php learn.php cleanup <repo> [--abandoned <NN-slug>] [--dry-run] [--no-gh]
 *                                                remove worktrees of merged lessons
 *
 * Needs PHP 8.3+ and Git. Standard library only.
 */

namespace Learn;

const MAX_STEPS = 6;
const MAX_GUIDE_TOKENS = 4000;
const CHARS_PER_TOKEN = 3.5; // Conservative estimate; PHP ships no tokenizer.
const PACKAGES = [
    'laravel/boost' => 'boost',
    'nwidart/laravel-modules' => 'modules',
    'deptrac/deptrac' => 'deptrac',
    'larastan/larastan' => 'larastan',
    'pestphp/pest' => 'pest',
    'laravel/sanctum' => 'sanctum',
    'knuckleswtf/scribe' => 'scribe',
    'torann/laravel-repository' => 'repository',
];

function readText(string $path): string
{
    $text = @file_get_contents($path);

    return $text === false ? '' : str_replace("\r\n", "\n", $text);
}

/** @return array<mixed> */
function readJson(string $path): array
{
    $data = json_decode(readText($path), true);

    return is_array($data) ? $data : [];
}

/** @param array<mixed> $data */
function dig(array $data, string ...$keys): mixed
{
    $value = $data;
    foreach ($keys as $key) {
        if (! is_array($value) || ! array_key_exists($key, $value)) {
            return null;
        }
        $value = $value[$key];
    }

    return $value;
}

/**
 * @param  list<string>  $command
 * @return array{int, string} exit code (127 when the program can't start) and combined output
 */
function run(array $command, string $cwd): array
{
    $process = @proc_open($command, [1 => ['pipe', 'w'], 2 => ['pipe', 'w']], $pipes, $cwd);
    if (! is_resource($process)) {
        return [127, "can't run $command[0]"];
    }
    $output = stream_get_contents($pipes[1]).stream_get_contents($pipes[2]);
    $code = proc_close($process);

    return [$code, trim(str_replace("\r\n", "\n", $output))];
}

/**
 * @param  list<string>  $arguments
 * @return array{int, string}
 */
function gh(array $arguments, string $cwd): array
{
    $program = getenv('LEARN_GH') ?: 'gh';
    $command = str_ends_with($program, '.php') ? [PHP_BINARY, $program] : [$program];

    return run([...$command, ...$arguments], $cwd);
}

function isLaravelApp(string $dir): bool
{
    $require = dig(readJson("$dir/composer.json"), 'require');

    return is_file("$dir/artisan") && is_array($require) && isset($require['laravel/framework']);
}

/** @return list<string> app folders, relative to the repo */
function findApps(string $repo): array
{
    $apps = isLaravelApp($repo) ? ['.'] : [];
    foreach (['*', '*/*'] as $pattern) {
        foreach (glob("$repo/$pattern", GLOB_ONLYDIR) ?: [] as $dir) {
            $relative = substr($dir, strlen($repo) + 1);
            if (preg_match('#(^|/)(vendor|node_modules|storage)(/|$)#', $relative) !== 1 && isLaravelApp($dir)) {
                $apps[] = $relative;
            }
        }
    }

    return $apps;
}

/** @return array<string, string> */
function frontmatter(string $path): array
{
    if (preg_match('/\A---\n(.*?)\n---/s', readText($path), $match) !== 1) {
        return [];
    }
    preg_match_all('/^(\w+):\s*(.+?)\s*$/m', $match[1], $pairs, PREG_SET_ORDER);

    return array_column($pairs, 2, 1);
}

/** Returns a PR number, '' when none is merged, or null when unknown. */
function mergedPr(string $repo, string $branch, bool $useGh): ?string
{
    if (! $useGh || $branch === '') {
        return null;
    }
    [$code, $output] = gh(['pr', 'list', '--head', $branch, '--state', 'merged', '--json', 'number', '--limit', '1'], $repo);
    $rows = json_decode($output, true);
    if ($code !== 0 || ! is_array($rows)) {
        return null;
    }
    $number = dig($rows, '0', 'number');

    return is_int($number) || is_string($number) ? (string) $number : '';
}

/** @return list<string> lesson folder paths, in order */
function lessonDirs(string $repo): array
{
    $dirs = array_filter(
        glob("$repo/learn/*", GLOB_ONLYDIR) ?: [],
        static fn (string $dir): bool => preg_match('/^\d+-/', basename($dir)) === 1,
    );
    sort($dirs);

    return $dirs;
}

function scanLessons(string $repo, bool $useGh): void
{
    $highest = 0;
    $finished = 0;
    foreach (lessonDirs($repo) as $lesson) {
        $name = basename($lesson);
        $highest = max($highest, (int) $name);
        $meta = frontmatter("$lesson/TICKET.md");
        $status = $meta['status'] ?? 'unknown';
        if (in_array($status, ['done', 'dropped'], true)) {
            $finished++;

            continue;
        }
        $pr = $status === 'in-progress' ? mergedPr($repo, $meta['branch'] ?? '', $useGh) : null;
        $note = $pr === null || $pr === '' ? '' : ", merged PR #$pr";
        echo "lesson $name: $status, ".($meta['kind'] ?? '?')."$note\n";
    }
    echo "lessons finished: $finished\n";
    echo 'next lesson number: '.sprintf('%02d', $highest + 1)."\n";
}

function modulesDir(string $app): string
{
    $include = dig(readJson("$app/composer.json"), 'extra', 'merge-plugin', 'include');
    foreach (is_array($include) ? $include : [] as $pattern) {
        if (is_string($pattern) && preg_match('#^(.+)/\*/composer\.json$#', $pattern, $match) === 1) {
            return trim($match[1], './');
        }
    }

    return 'Modules';
}

function countFiles(string $dir, string $suffix): int
{
    if (! is_dir($dir)) {
        return 0;
    }
    $count = 0;
    $files = new \RecursiveIteratorIterator(new \RecursiveDirectoryIterator($dir, \FilesystemIterator::SKIP_DOTS));
    foreach ($files as $file) {
        if ($file instanceof \SplFileInfo && str_ends_with($file->getFilename(), $suffix)) {
            $count++;
        }
    }

    return $count;
}

function normalise(string $uri): string
{
    return '/'.trim((string) preg_replace('/\{[^}]*\}/', '{}', $uri), '/');
}

/** @return list<array{string, string}> method and normalised path of each endpoint in a plan */
function planRoutes(string $text): array
{
    preg_match_all('/^\|\s*(GET|POST|PUT|PATCH|DELETE)\s*\|\s*`([^`]+)`/m', $text, $rows, PREG_SET_ORDER);

    return array_map(static fn (array $row): array => [$row[1], normalise($row[2])], $rows);
}

/** @return list<string> */
function planItems(string $text): array
{
    if (preg_match('/^## Build order\n(.*?)(?=^## |\z)/ms', $text, $match) !== 1) {
        return [];
    }
    preg_match_all('/^\s*(\d+\.\s+.+?|- \[[ x]\]\s+.+?)\s*$/m', $match[1], $items);

    return $items[1];
}

function testsText(string $app, string $modules): string
{
    $text = '';
    foreach (["$app/tests", "$app/$modules"] as $dir) {
        if (! is_dir($dir)) {
            continue;
        }
        $files = new \RecursiveIteratorIterator(new \RecursiveDirectoryIterator($dir, \FilesystemIterator::SKIP_DOTS));
        foreach ($files as $file) {
            if ($file instanceof \SplFileInfo && str_ends_with($file->getFilename(), 'Test.php')) {
                $text .= readText($file->getPathname());
            }
        }
    }

    return $text;
}

function isTested(string $uri, string $tests): bool
{
    $pattern = implode('[^/\'"]+', array_map(static fn (string $part): string => preg_quote($part, '#'), explode('{}', normalise($uri))));

    return preg_match("#$pattern(?![\\w/-])#", $tests) === 1;
}

/** @param array<mixed> $config */
function scanApp(string $repo, string $relative, array $config): void
{
    $app = $relative === '.' ? $repo : "$repo/$relative";
    echo "app: $relative\n";
    $composer = readJson("$app/composer.json");
    $required = array_merge(
        is_array($composer['require'] ?? null) ? $composer['require'] : [],
        is_array($composer['require-dev'] ?? null) ? $composer['require-dev'] : [],
    );
    $version = '?';
    $locked = dig(readJson("$app/composer.lock"), 'packages');
    foreach (is_array($locked) ? $locked : [] as $package) {
        if (is_array($package) && ($package['name'] ?? null) === 'laravel/framework' && is_string($package['version'] ?? null)) {
            $version = ltrim($package['version'], 'v');
        }
    }
    echo "laravel: $version; php: ".(is_string($required['php'] ?? null) ? $required['php'] : '?')."\n";
    $has = array_values(array_intersect_key(PACKAGES, $required));
    $missing = array_values(array_diff_key(PACKAGES, $required));
    echo 'packages: '.(implode(', ', $has) ?: 'none').($missing === [] ? '' : '; not installed: '.implode(', ', $missing))."\n";
    if (! isset($required['laravel/boost'])) {
        echo "blocker: no_boost (owner runs: composer require --dev laravel/boost, then php artisan boost:install)\n";
    }

    $modules = modulesDir($app);
    $names = [];
    foreach (glob("$app/$modules/*/module.json") ?: [] as $manifest) {
        $dir = dirname($manifest);
        $names[] = basename($dir).' (controllers '.countFiles("$dir/app/Http/Controllers", 'Controller.php')
            .', models '.countFiles("$dir/app/Models", '.php').', tests '.countFiles("$dir/tests", 'Test.php').')';
    }
    echo "modules in $modules: ".(implode(', ', $names) ?: 'none')."\n";

    $tests = testsText($app, $modules);
    $existing = [];
    if (! is_dir("$app/vendor")) {
        echo "routes: unavailable (no vendor folder; owner runs composer install)\n";
    } else {
        [$code, $output] = run([PHP_BINARY, 'artisan', 'route:list', '--json', '--except-vendor'], $app);
        $routes = json_decode($output, true);
        if ($code !== 0 || ! is_array($routes)) {
            echo 'routes: unavailable ('.substr(strtok($output, "\n") ?: 'no output', 0, 160).")\n";
        } else {
            foreach ($routes as $route) {
                if (! is_array($route) || ! is_string($route['uri'] ?? null) || ! is_string($route['method'] ?? null)) {
                    continue;
                }
                $method = explode('|', $route['method'])[0];
                $existing["$method ".normalise($route['uri'])] = true;
                $middleware = implode(',', array_filter((array) ($route['middleware'] ?? []), 'is_string'));
                $guarded = preg_match('/auth|Authenticate/i', $middleware) === 1;
                $notes = [$guarded ? 'auth' : 'public'];
                if ($method !== 'GET' && ! $guarded) {
                    $notes[] = 'hint: public write';
                }
                if (! isTested($route['uri'], $tests)) {
                    $notes[] = 'hint: no test names this path';
                }
                $action = is_string($route['action'] ?? null) ? preg_replace('/^.*\\\\/', '', $route['action']) : '?';
                echo "route $method /".trim($route['uri'], '/')." -> $action [".implode('; ', $notes)."]\n";
            }
            echo 'routes: '.count($existing)."\n";
        }
    }

    $plan = is_string($config['planDoc'] ?? null) ? readText("$repo/".$config['planDoc']) : '';
    if ($plan === '') {
        echo "plan: none\n";

        return;
    }
    foreach (planRoutes($plan) as [$method, $path]) {
        if (! isset($existing["$method $path"])) {
            echo "planned, not built: $method $path\n";
        }
    }
    foreach (planItems($plan) as $item) {
        echo "plan step: $item\n";
    }
}

function scan(string $repo, bool $useGh): int
{
    [$code, $output] = run(['git', 'rev-parse', '--is-inside-work-tree'], $repo);
    if ($code === 127) {
        echo "blocker: git_unavailable $output\n";
    } elseif ($code !== 0) {
        echo str_contains($output, 'not a git') ? "blocker: no_git\n" : 'blocker: git_unavailable '.substr($output, 0, 200)."\n";
    } elseif (run(['git', 'rev-parse', '--verify', 'HEAD'], $repo)[0] !== 0) {
        echo "blocker: no_commits\n";
    }
    $configPath = "$repo/learn/learn.config.json";
    $config = [];
    if (is_file($configPath)) {
        $config = json_decode(readText($configPath), true);
        if (! is_array($config) || array_is_list($config)) {
            fwrite(STDERR, "error: $configPath: must be a JSON object\n");

            return 2;
        }
    } else {
        echo "blocker: no_config\n";
    }
    $configured = $config['appRoot'] ?? null;
    if (is_string($configured)) {
        $apps = isLaravelApp($configured === '.' ? $repo : "$repo/$configured") ? [$configured] : [];
    } else {
        $apps = findApps($repo);
    }
    if ($apps === []) {
        echo "blocker: no_laravel_app (empty repo: scaffold lesson; otherwise check appRoot)\n";
    } elseif (count($apps) > 1) {
        echo 'blocker: several_apps '.implode(', ', $apps)." (ask which, then set appRoot)\n";
    } else {
        scanApp($repo, $apps[0], $config);
    }
    scanLessons($repo, $useGh);
    preg_match_all('/^## /m', readText("$repo/learn/php-concepts.md"), $headings);
    echo 'php concepts seen: '.count($headings[0])."\n";

    return 0;
}

/** @return array<int, string> step number => its text */
function splitSteps(string $text): array
{
    $steps = [];
    $parts = preg_split('/^(?=## )/m', $text) ?: [];
    foreach ($parts as $part) {
        if (preg_match('/\A## Step (\d+)\b/', $part, $match) === 1) {
            $steps[(int) $match[1]] = rtrim($part);
        }
    }

    return $steps;
}

function showStep(string $guide, int $number): int
{
    $steps = splitSteps(readText($guide));
    if (isset($steps[$number])) {
        echo $steps[$number]."\n";

        return 0;
    }
    fwrite(STDERR, "no step $number; the guide has steps up to ".($steps === [] ? 0 : max(array_keys($steps)))."\n");

    return 1;
}

function guideSize(string $guide): int
{
    $text = readText($guide);
    $count = count(splitSteps($text));
    $tokens = (int) round(mb_strlen($text) / CHARS_PER_TOKEN);
    echo "steps: $count/".MAX_STEPS."; estimated tokens: $tokens/".MAX_GUIDE_TOKENS."\n";
    if ($count > MAX_STEPS || $tokens > MAX_GUIDE_TOKENS) {
        echo "over limit: split the ticket or shorten the guide\n";

        return 1;
    }

    return 0;
}

function canonical(string $path): string
{
    $real = realpath($path);
    $path = rtrim(str_replace('\\', '/', $real === false ? $path : $real), '/');

    return PHP_OS_FAMILY === 'Windows' ? strtolower($path) : $path;
}

/** @return list<string> canonical paths of the repo's linked worktrees, without the main one */
function linkedWorktrees(string $repo): array
{
    [$code, $output] = run(['git', 'worktree', 'list', '--porcelain'], $repo);
    if ($code !== 0) {
        return [];
    }
    preg_match_all('/^worktree (.+)$/m', $output, $match);

    return array_map(canonical(...), array_slice($match[1], 1));
}

function cleanup(string $repo, ?string $abandoned, bool $dryRun, bool $useGh): int
{
    $lessons = lessonDirs($repo);
    if ($abandoned !== null && ! in_array($abandoned, array_map('basename', $lessons), true)) {
        fwrite(STDERR, "error: no lesson named $abandoned\n");

        return 2;
    }
    $worktrees = linkedWorktrees($repo);
    $failed = false;
    foreach ($lessons as $lesson) {
        $name = basename($lesson);
        if (preg_match('/^- Worktree: (.+?)\s*$/m', readText("$lesson/README.md"), $match) !== 1 || ! file_exists($match[1])) {
            continue;
        }
        $path = $match[1];
        if (canonical($path) === canonical($repo) || str_starts_with(canonical($path).'/', canonical($repo).'/')) {
            echo "keep $name: recorded path is inside the repo, not a lesson worktree\n";

            continue;
        }
        if (! in_array(canonical($path), $worktrees, true)) {
            echo "keep $name: $path is not a registered worktree of this repo\n";

            continue;
        }
        if ($name !== $abandoned) {
            $pr = mergedPr($repo, frontmatter("$lesson/TICKET.md")['branch'] ?? '', $useGh);
            if ($pr === null || $pr === '') {
                echo "keep $name: ".($pr === null ? 'merge state unknown, ask the owner' : 'no merged PR, ask the owner before removing')."\n";

                continue;
            }
        }
        if ($dryRun) {
            echo "would remove $path\n";

            continue;
        }
        [$code, $output] = run(['git', 'worktree', 'remove', '--force', $path], $repo);
        if ($code !== 0) {
            echo "failed to remove $path: $output\n";
            $failed = true;

            continue;
        }
        echo "removed $path\n";
        $parent = dirname($path);
        if (str_ends_with($parent, '-lessons') && count(scandir($parent) ?: []) === 2) {
            rmdir($parent);
            echo "removed empty $parent\n";
        }
    }
    if (! $dryRun) {
        run(['git', 'worktree', 'prune'], $repo);
    }

    return $failed ? 1 : 0;
}

function usage(): int
{
    fwrite(STDERR, "usage: php learn.php scan <repo> [--no-gh] | step <GUIDE.md> <number> | guide-size <GUIDE.md> | cleanup <repo> [--abandoned <NN-slug>] [--dry-run] [--no-gh]\n");

    return 2;
}

/** @param list<string> $argv */
function main(array $argv): int
{
    $flags = [];
    $positional = [];
    for ($i = 1; $i < count($argv); $i++) {
        if ($argv[$i] === '--abandoned') {
            $flags['--abandoned'] = $argv[++$i] ?? '';
        } elseif (str_starts_with($argv[$i], '--')) {
            $flags[$argv[$i]] = '1';
        } else {
            $positional[] = $argv[$i];
        }
    }
    [$command, $target] = [$positional[0] ?? '', $positional[1] ?? ''];
    if (in_array($command, ['scan', 'cleanup'], true)) {
        $repo = realpath($target);
        if ($target === '' || $repo === false || ! is_dir($repo)) {
            fwrite(STDERR, "error: $target: not a directory\n");

            return 2;
        }
        $repo = str_replace('\\', '/', $repo);
        $useGh = ! isset($flags['--no-gh']);

        return $command === 'scan' ? scan($repo, $useGh) : cleanup($repo, $flags['--abandoned'] ?? null, isset($flags['--dry-run']), $useGh);
    }
    if (in_array($command, ['step', 'guide-size'], true)) {
        if (! is_file($target)) {
            fwrite(STDERR, "error: $target: no such file\n");

            return 2;
        }
        if ($command === 'guide-size') {
            return guideSize($target);
        }

        return ctype_digit($positional[2] ?? '') ? showStep($target, (int) $positional[2]) : usage();
    }

    return usage();
}

$script = $_SERVER['SCRIPT_FILENAME'] ?? null;
if (PHP_SAPI === 'cli' && is_string($script) && realpath($script) === __FILE__) {
    $arguments = $_SERVER['argv'] ?? null;
    exit(main(array_values(array_filter(is_array($arguments) ? $arguments : [], 'is_string'))));
}
