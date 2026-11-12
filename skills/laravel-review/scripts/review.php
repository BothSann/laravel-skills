<?php

declare(strict_types=1);

/**
 * Helpers for the laravel-review skill. Run from inside the repo under review.
 *
 *   php review.php context <pr>                  what to review: range, open threads, rule sources
 *   php review.php preview <pr> <findings.json>  validate findings and print the review, post nothing
 *   php review.php post <pr> <findings.json>     post one review of inline comments
 *   php review.php clean <pr>                    post the "no issues found" comment
 *
 * findings.json is a list of {"severity": "P1|P2|P3", "title", "body", "path", "line", "source"}.
 * "source" names the rule a P3 breaks. Reviews are always event COMMENT: never approve or reject.
 * Needs PHP 8.3+, Git, and an authenticated GitHub CLI. Standard library only.
 */

namespace Review;

const CLEAN_MARKER = '<!-- laravel-review:clean -->';
const THREADS_QUERY = 'query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){reviewThreads(first:100){nodes{isResolved path line originalLine comments(first:1){nodes{author{login} body}}}}}}}';
const RULE_FILES = ['AGENTS.md', 'CLAUDE.md', '.ai/guidelines', '.ai/rules', '.cursor/rules', '.github/copilot-instructions.md', 'docs/rules'];
const LAYERS = [
    'laravel/boost' => 'boost',
    'nwidart/laravel-modules' => 'modules',
    'torann/laravel-repository' => 'repository',
    'laravel/sanctum' => 'sanctum',
    'pestphp/pest' => 'pest',
];

final class Stop extends \RuntimeException {}

final class Pr
{
    public function __construct(
        public readonly int $number,
        public readonly string $repo,
        public readonly string $head,
        public readonly string $headBranch,
        public readonly string $baseBranch,
        public readonly string $state,
    ) {}
}

final class Finding
{
    public function __construct(
        public readonly string $severity,
        public readonly string $title,
        public readonly string $body,
        public readonly string $path,
        public readonly int $line,
    ) {}

    public function heading(): string
    {
        return "$this->severity — $this->title";
    }

    public function comment(): string
    {
        return "**{$this->heading()}.** $this->body";
    }
}

/**
 * @param  list<string>  $command
 * @return array{int, string} exit code (127 when the program can't start) and combined output
 */
function run(array $command): array
{
    $process = @proc_open($command, [1 => ['pipe', 'w'], 2 => ['pipe', 'w']], $pipes);
    if (! is_resource($process)) {
        return [127, "can't run $command[0]"];
    }
    $output = stream_get_contents($pipes[1]).stream_get_contents($pipes[2]);
    $code = proc_close($process);

    return [$code, trim(str_replace("\r\n", "\n", $output))];
}

/** @param list<string> $arguments */
function gh(array $arguments): string
{
    $program = getenv('REVIEW_GH') ?: 'gh';
    $command = str_ends_with($program, '.php') ? [PHP_BINARY, $program] : [$program];
    [$code, $output] = run([...$command, ...$arguments]);
    if ($code !== 0) {
        throw new Stop('gh '.implode(' ', array_slice($arguments, 0, 3)).' failed: '.substr($output, 0, 300));
    }

    return $output;
}

/**
 * @param  list<string>  $arguments
 * @return array<mixed>
 */
function ghJson(array $arguments): array
{
    $data = json_decode(gh($arguments), true);
    if (! is_array($data)) {
        throw new Stop('gh '.implode(' ', array_slice($arguments, 0, 3)).' did not return JSON');
    }

    return $data;
}

/** @param array<mixed> $data */
function dig(array $data, string|int ...$keys): mixed
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

function text(mixed $value): string
{
    return is_string($value) ? $value : '';
}

function loadPr(string $number): Pr
{
    if (! ctype_digit($number)) {
        throw new Stop("\"$number\" is not a pull request number");
    }
    $data = ghJson(['pr', 'view', $number, '--json', 'number,state,headRefOid,headRefName,baseRefName,url']);
    if (preg_match('#github\.com/([^/]+/[^/]+)/pull/#', text($data['url'] ?? null), $match) !== 1) {
        throw new Stop('could not read the repository from the pull request URL');
    }

    return new Pr((int) $number, $match[1], text($data['headRefOid'] ?? null), text($data['headRefName'] ?? null), text($data['baseRefName'] ?? null), text($data['state'] ?? null));
}

function reviewer(): string
{
    return trim(gh(['api', 'user', '--jq', '.login']));
}

/** @return list<array{commit: string, body: string}> the reviewer's earlier reviews, oldest first */
function ownReviews(Pr $pr, string $reviewer): array
{
    $reviews = [];
    foreach (ghJson(['api', "repos/$pr->repo/pulls/$pr->number/reviews", '--paginate', '--slurp']) as $page) {
        foreach (is_array($page) ? $page : [] as $review) {
            if (is_array($review) && dig($review, 'user', 'login') === $reviewer) {
                $reviews[] = ['commit' => text($review['commit_id'] ?? null), 'body' => text($review['body'] ?? null)];
            }
        }
    }

    return $reviews;
}

/** @return list<array{path: string, line: int, heading: string}> the reviewer's unresolved threads */
function openThreads(Pr $pr, string $reviewer): array
{
    [$owner, $name] = explode('/', $pr->repo);
    $data = ghJson(['api', 'graphql', '-f', 'query='.THREADS_QUERY, '-F', "owner=$owner", '-F', "name=$name", '-F', "number=$pr->number"]);
    $nodes = dig($data, 'data', 'repository', 'pullRequest', 'reviewThreads', 'nodes');
    $threads = [];
    foreach (is_array($nodes) ? $nodes : [] as $node) {
        if (! is_array($node) || ($node['isResolved'] ?? false) === true || dig($node, 'comments', 'nodes', 0, 'author', 'login') !== $reviewer) {
            continue;
        }
        $line = $node['line'] ?? $node['originalLine'] ?? 0;
        $threads[] = [
            'path' => text($node['path'] ?? null),
            'line' => is_int($line) ? $line : 0,
            'heading' => heading(text(dig($node, 'comments', 'nodes', 0, 'body'))),
        ];
    }

    return $threads;
}

/** The "P1 — Title" part of a comment, or its first words when it has none. */
function heading(string $comment): string
{
    if (preg_match('/^\*\*(P[123] — .+?)\.\*\*/u', $comment, $match) === 1) {
        return $match[1];
    }

    return mb_substr(strtok($comment, "\n") ?: '', 0, 60);
}

function sameHeading(string $left, string $right): bool
{
    $plain = static fn (string $value): string => mb_strtolower((string) preg_replace('/[^\p{L}\p{N}]+/u', ' ', $value));

    return trim($plain($left)) === trim($plain($right));
}

/**
 * Lines a review comment may attach to: added and context lines on the new side of each hunk.
 *
 * @return array<string, array{added: int, removed: int, lines: array<int, true>}> keyed by path
 */
function parseDiff(string $diff): array
{
    $added = [];
    $removed = [];
    $lines = [];
    $path = null;
    $line = 0;
    foreach (explode("\n", $diff) as $row) {
        if (str_starts_with($row, 'diff --git ')) {
            $path = null;
        } elseif (str_starts_with($row, '+++ ')) {
            $path = $row === '+++ /dev/null' ? null : substr($row, 6);
            if ($path !== null) {
                $added[$path] = 0;
                $removed[$path] = 0;
                $lines[$path] = [];
            }
        } elseif (preg_match('/^@@ -\d+(?:,\d+)? \+(\d+)/', $row, $match) === 1) {
            $line = (int) $match[1];
        } elseif ($path !== null && $line > 0 && $row !== '' && ! str_starts_with($row, '\\')) {
            if ($row[0] === '-') {
                $removed[$path]++;

                continue;
            }
            if ($row[0] === '+') {
                $added[$path]++;
            }
            $lines[$path][$line++] = true;
        }
    }
    $files = [];
    foreach ($lines as $name => $commentable) {
        $files[$name] = ['added' => $added[$name], 'removed' => $removed[$name], 'lines' => $commentable];
    }

    return $files;
}

/** @return list<Finding> */
function loadFindings(string $file): array
{
    $data = json_decode((string) @file_get_contents($file), true);
    if (! is_array($data) || ! array_is_list($data)) {
        throw new Stop("$file must hold a JSON list of findings");
    }
    $findings = [];
    $errors = [];
    foreach ($data as $index => $item) {
        $label = 'finding '.($index + 1);
        if (! is_array($item)) {
            $errors[] = "$label: must be an object";

            continue;
        }
        $severity = text($item['severity'] ?? null);
        $title = rtrim(trim(text($item['title'] ?? null)), '.');
        $body = trim(text($item['body'] ?? null));
        $path = ltrim(str_replace('\\', '/', text($item['path'] ?? null)), '/');
        $line = $item['line'] ?? null;
        if (! in_array($severity, ['P1', 'P2', 'P3'], true)) {
            $errors[] = "$label: severity must be P1, P2 or P3";
        }
        if ($title === '' || $body === '' || $path === '') {
            $errors[] = "$label: title, body and path are required";
        }
        if (! is_int($line) || $line < 1) {
            $errors[] = "$label: line must be a positive number";
        }
        if ($severity === 'P3' && trim(text($item['source'] ?? null)) === '') {
            $errors[] = "$label: a P3 needs \"source\", the rule it breaks";
        }
        if (is_int($line)) {
            $findings[] = new Finding($severity, $title, $body, $path, $line);
        }
    }
    if ($errors !== []) {
        throw new Stop("invalid findings:\n  ".implode("\n  ", $errors));
    }
    usort($findings, static fn (Finding $a, Finding $b): int => [$a->severity, $a->path, $a->line] <=> [$b->severity, $b->path, $b->line]);

    return $findings;
}

/**
 * @param  list<Finding>  $findings
 * @param  list<array{path: string, line: int, heading: string}>  $threads
 * @return array{inline: list<Finding>, outside: list<Finding>, skipped: list<Finding>}
 */
function sort(array $findings, string $diff, array $threads): array
{
    $files = parseDiff($diff);
    $groups = ['inline' => [], 'outside' => [], 'skipped' => []];
    foreach ($findings as $finding) {
        $duplicate = array_filter($threads, static fn (array $thread): bool => $thread['path'] === $finding->path && sameHeading($thread['heading'], $finding->heading()));
        $group = match (true) {
            $duplicate !== [] => 'skipped',
            isset($files[$finding->path]['lines'][$finding->line]) => 'inline',
            default => 'outside',
        };
        $groups[$group][] = $finding;
    }

    return $groups;
}

/**
 * @param  array{inline: list<Finding>, outside: list<Finding>, skipped: list<Finding>}  $groups
 * @return array{commit_id: string, event: string, body: string, comments: list<array{path: string, line: int, side: string, body: string}>}
 */
function payload(Pr $pr, array $groups): array
{
    $body = '';
    if ($groups['outside'] !== []) {
        $body = "Findings on lines this pull request does not change:\n";
        foreach ($groups['outside'] as $finding) {
            $body .= "\n- `$finding->path:$finding->line` {$finding->comment()}";
        }
    }
    $comments = array_map(
        static fn (Finding $finding): array => ['path' => $finding->path, 'line' => $finding->line, 'side' => 'RIGHT', 'body' => $finding->comment()],
        $groups['inline'],
    );

    return ['commit_id' => $pr->head, 'event' => 'COMMENT', 'body' => $body, 'comments' => $comments];
}

/** @param array<mixed> $payload */
function send(Pr $pr, array $payload): void
{
    $file = tempnam(sys_get_temp_dir(), 'review');
    if ($file === false) {
        throw new Stop('could not create a temporary file');
    }
    try {
        file_put_contents($file, json_encode($payload, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR));
        gh(['api', '--method', 'POST', "repos/$pr->repo/pulls/$pr->number/reviews", '--input', $file, '--silent']);
    } finally {
        @unlink($file);
    }
}

function context(Pr $pr): int
{
    $reviewer = reviewer();
    $reviews = ownReviews($pr, $reviewer);
    $last = $reviews === [] ? '' : $reviews[count($reviews) - 1]['commit'];
    echo "pr: #$pr->number $pr->headBranch -> $pr->baseBranch, ".strtolower($pr->state).', head '.substr($pr->head, 0, 7)."\n";
    echo "reviewer: $reviewer\n";
    if ($last === '') {
        echo "last review: none\nreview: the whole pull request (gh pr diff $pr->number)\n";
    } elseif ($last === $pr->head) {
        echo 'last review: '.substr($last, 0, 7)." (the current head)\nreview: nothing new since your last review\n";
    } elseif (run(['git', 'cat-file', '-e', "$last^{commit}"])[0] === 0 && run(['git', 'merge-base', '--is-ancestor', $last, $pr->head])[0] === 0) {
        echo 'last review: '.substr($last, 0, 7)."\nreview: only new commits (git diff $last..$pr->head)\n";
    } else {
        echo 'last review: '.substr($last, 0, 7)." (rewritten or not fetched)\nreview: the whole pull request (gh pr diff $pr->number)\n";
    }

    $threads = openThreads($pr, $reviewer);
    echo 'your open threads: '.count($threads)."\n";
    foreach ($threads as $thread) {
        echo "  {$thread['path']}:{$thread['line']} {$thread['heading']}\n";
    }

    $composer = json_decode((string) @file_get_contents('composer.json'), true);
    $required = is_array($composer) ? array_merge((array) ($composer['require'] ?? []), (array) ($composer['require-dev'] ?? [])) : [];
    echo 'layers: '.(implode(', ', array_values(array_intersect_key(LAYERS, $required))) ?: 'none')."\n";
    if (! isset($required['laravel/boost'])) {
        echo "warning: Laravel Boost is not installed, so its rules can't be loaded from this project\n";
    }
    echo 'rule sources: '.(implode(', ', array_values(array_filter(RULE_FILES, 'file_exists'))) ?: 'none')."\n";

    $files = parseDiff(gh(['pr', 'diff', (string) $pr->number]));
    echo 'changed files: '.count($files)."\n";
    foreach ($files as $path => $file) {
        echo "  $path (+{$file['added']} -{$file['removed']})\n";
    }

    return 0;
}

function review(Pr $pr, string $file, bool $post): int
{
    $groups = sort(loadFindings($file), gh(['pr', 'diff', (string) $pr->number]), openThreads($pr, reviewer()));
    $payload = payload($pr, $groups);
    foreach ($payload['comments'] as $comment) {
        echo "{$comment['path']}:{$comment['line']}\n  {$comment['body']}\n\n";
    }
    if ($payload['body'] !== '') {
        echo $payload['body']."\n\n";
    }
    foreach ($groups['skipped'] as $finding) {
        echo "skipped, already has an open thread: $finding->path {$finding->heading()}\n";
    }
    $summary = count($groups['inline']).' inline, '.count($groups['outside']).' outside the changed lines, '.count($groups['skipped']).' skipped';
    if ($payload['comments'] === [] && $payload['body'] === '') {
        echo "nothing new to post ($summary)\n";

        return 0;
    }
    if (! $post) {
        echo "preview only, nothing posted ($summary)\n";

        return 0;
    }
    send($pr, $payload);
    echo "posted one review on #$pr->number at ".substr($pr->head, 0, 7)." ($summary)\n";

    return 0;
}

function clean(Pr $pr): int
{
    $reviewer = reviewer();
    foreach (ownReviews($pr, $reviewer) as $review) {
        if ($review['commit'] === $pr->head && str_contains($review['body'], CLEAN_MARKER)) {
            echo 'already posted for '.substr($pr->head, 0, 7).", nothing to do\n";

            return 0;
        }
    }
    $open = count(openThreads($pr, $reviewer));
    $threads = $open === 0 ? '' : " $open earlier thread".($open === 1 ? ' is' : 's are').' still open for the author to resolve.';
    $body = '**No issues found** at `'.substr($pr->head, 0, 7)."`.$threads Ready to merge once a person approves.\n\n".CLEAN_MARKER;
    send($pr, ['commit_id' => $pr->head, 'event' => 'COMMENT', 'body' => $body, 'comments' => []]);
    echo "posted the no-issues comment on #$pr->number at ".substr($pr->head, 0, 7)."\n";

    return 0;
}

/** @param list<string> $argv */
function main(array $argv): int
{
    [$command, $number, $file] = [$argv[1] ?? '', $argv[2] ?? '', $argv[3] ?? ''];
    try {
        return match (true) {
            $command === 'context' && $number !== '' => context(loadPr($number)),
            in_array($command, ['preview', 'post'], true) && $file !== '' => review(loadPr($number), $file, $command === 'post'),
            $command === 'clean' && $number !== '' => clean(loadPr($number)),
            default => throw new Stop('usage: php review.php context <pr> | preview <pr> <findings.json> | post <pr> <findings.json> | clean <pr>'),
        };
    } catch (Stop $stop) {
        fwrite(STDERR, 'error: '.$stop->getMessage()."\n");

        return 2;
    }
}

$script = $_SERVER['SCRIPT_FILENAME'] ?? null;
if (PHP_SAPI === 'cli' && is_string($script) && realpath($script) === __FILE__) {
    $arguments = $_SERVER['argv'] ?? null;
    exit(main(array_values(array_filter(is_array($arguments) ? $arguments : [], 'is_string'))));
}
