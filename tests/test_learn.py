"""Behaviour of learn.php and the laravel-learn docs. Run: python -m unittest discover -s tests

Needs `php` on PATH, or its path in the PHP environment variable, and Git. The real `gh` and a
real Laravel app are never run: a stand-in `artisan` prints routes, and LEARN_GH names a stand-in.
"""

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).parents[1]
SKILL = REPO / "skills" / "laravel-learn"
SCRIPT = SKILL / "scripts" / "learn.php"
API_RULES = REPO / "skills" / "laravel-api-practices" / "rules"
PHP = os.environ.get("PHP", "php")
# Rule files in Laravel Boost 2.10's laravel-best-practices skill.
BOOST_RULES = {
    "advanced-queries",
    "architecture",
    "blade-views",
    "caching",
    "collections",
    "config",
    "db-performance",
    "eloquent",
    "error-handling",
    "events-notifications",
    "http-client",
    "mail",
    "migrations",
    "queue-jobs",
    "routing",
    "scheduling",
    "security",
    "style",
    "validation",
}
ROUTES = [
    {
        "method": "GET|HEAD",
        "uri": "api/v1/posts",
        "action": "App\\Http\\PostController@index",
        "middleware": ["api"],
    },
    {
        "method": "POST",
        "uri": "api/v1/posts",
        "action": "App\\Http\\PostController@store",
        "middleware": ["api", "Illuminate\\Auth\\Middleware\\Authenticate:sanctum"],
    },
    {"method": "DELETE", "uri": "api/v1/posts/{post}", "action": "Closure", "middleware": ["api"]},
]


def learn(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PHP, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, **(env or {})},
    )


def git(repo: Path, *args: str) -> None:
    identity = ["-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false"]
    subprocess.run(["git", *identity, *args], cwd=repo, check=True, capture_output=True)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode())


def make_app(
    root: Path, *, boost: bool = True, routes: object = ROUTES, vendor: bool = True
) -> Path:
    """A folder that looks like a Laravel app, with an artisan that prints the given routes."""
    dev = {"laravel/boost": "^2.10", "pestphp/pest": "^5.0"} if boost else {"pestphp/pest": "^5.0"}
    write(
        root / "composer.json",
        json.dumps({"require": {"php": "^8.3", "laravel/framework": "^13.0"}, "require-dev": dev}),
    )
    write(
        root / "composer.lock",
        json.dumps({"packages": [{"name": "laravel/framework", "version": "v13.42.0"}]}),
    )
    body = (
        "fwrite(STDERR, 'boot failed');\nexit(1);"
        if routes is None
        else f"echo {json.dumps(json.dumps(routes))};"
    )
    write(root / "artisan", f"<?php\nif (($argv[1] ?? '') === 'route:list') {{\n    {body}\n}}\n")
    if vendor:
        (root / "vendor").mkdir(parents=True, exist_ok=True)
    return root


class Base(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(folder.cleanup)
        self.tmp = Path(folder.name).resolve()
        self.repo = self.tmp / "repo"
        self.repo.mkdir()

    def init(self) -> None:
        git(self.repo, "init", "-q", "-b", "main")

    def commit(self) -> None:
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "c")

    def config(self, **fields: object) -> None:
        write(self.repo / "learn" / "learn.config.json", json.dumps(fields))

    def scan(self, **env: str) -> str:
        result = learn("scan", str(self.repo), "--no-gh", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout


class Scan(Base):
    def test_empty_folder_reports_blockers_for_scaffold(self) -> None:
        out = self.scan()
        for blocker in ("no_git", "no_config", "no_laravel_app"):
            self.assertIn(f"blocker: {blocker}", out)
        self.assertIn("next lesson number: 01", out)

    def test_repo_without_commits_is_reported(self) -> None:
        self.init()
        self.assertIn("blocker: no_commits", self.scan())

    def test_app_facts_and_packages(self) -> None:
        make_app(self.repo)
        out = self.scan()
        self.assertIn("app: .\n", out)
        self.assertIn("laravel: 13.42.0; php: ^8.3", out)
        self.assertIn("packages: boost, pest; not installed: modules,", out)
        self.assertNotIn("no_boost", out)

    def test_missing_boost_is_a_blocker(self) -> None:
        make_app(self.repo, boost=False)
        self.assertIn("blocker: no_boost", self.scan())

    def test_monorepo_finds_the_api_and_ignores_other_folders(self) -> None:
        make_app(self.repo / "apps" / "api")
        write(self.repo / "apps" / "web" / "package.json", "{}")
        make_app(self.repo / "apps" / "api" / "vendor" / "some" / "package")
        self.assertIn("app: apps/api\n", self.scan())

    def test_several_apps_ask(self) -> None:
        make_app(self.repo / "api")
        make_app(self.repo / "admin")
        self.assertIn("blocker: several_apps admin, api", self.scan())

    def test_configured_app_root_wins(self) -> None:
        make_app(self.repo / "api")
        make_app(self.repo / "admin")
        self.config(appRoot="api")
        out = self.scan()
        self.assertIn("app: api\n", out)
        self.assertNotIn("several_apps", out)

    def test_routes_hints_and_plan_coverage(self) -> None:
        make_app(self.repo)
        write(
            self.repo / "tests" / "Feature" / "PostTest.php",
            "<?php\n$this->getJson('/api/v1/posts');\n",
        )
        write(
            self.repo / "docs" / "plan.md",
            "## 1. Post\n| Method | Path | Auth | Does |\n|---|---|---|---|\n"
            "| GET | `/api/v1/posts` | public | List |\n"
            "| DELETE | `/api/v1/posts/{id}` | user | Delete |\n"
            "| POST | `/api/v1/posts/{id}/likes` | user | Like |\n\n"
            "## Build order\n1. Post\n2. Reaction\n\n## Later\n1. Not a step\n",
        )
        self.config(planDoc="docs/plan.md")
        out = self.scan()
        self.assertIn("route GET /api/v1/posts -> PostController@index [public]\n", out)
        self.assertIn("route POST /api/v1/posts -> PostController@store [auth]\n", out)
        self.assertIn(
            "route DELETE /api/v1/posts/{post} -> Closure "
            "[public; hint: public write; hint: no test names this path]\n",
            out,
        )
        self.assertIn("routes: 3\n", out)
        self.assertIn("planned, not built: POST /api/v1/posts/{}/likes", out)
        self.assertNotIn("planned, not built: DELETE", out)
        self.assertIn("plan step: 1. Post\nplan step: 2. Reaction\n", out)
        self.assertNotIn("Not a step", out)

    def test_a_longer_path_does_not_count_as_a_test_of_a_shorter_one(self) -> None:
        make_app(self.repo)
        write(self.repo / "tests" / "Feature" / "LikeTest.php", "<?php\n'/api/v1/posts/1/likes';\n")
        out = self.scan()
        self.assertIn("PostController@index [public; hint: no test names this path]", out)

    def test_app_that_fails_to_boot_is_reported_not_fatal(self) -> None:
        make_app(self.repo, routes=None)
        self.assertIn("routes: unavailable (boot failed)", self.scan())

    def test_app_without_vendor_is_reported(self) -> None:
        make_app(self.repo, vendor=False)
        self.assertIn("routes: unavailable (no vendor folder", self.scan())

    def test_modules_are_listed_with_counts(self) -> None:
        make_app(self.repo)
        post = self.repo / "Modules" / "Post"
        write(post / "module.json", '{"name": "Post"}')
        write(post / "app" / "Http" / "Controllers" / "PostController.php", "<?php\n")
        write(post / "app" / "Models" / "Post.php", "<?php\n")
        write(post / "tests" / "Feature" / "PostTest.php", "<?php\n")
        self.assertIn("modules in Modules: Post (controllers 1, models 1, tests 1)", self.scan())

    def test_invalid_config_stops(self) -> None:
        write(self.repo / "learn" / "learn.config.json", "[1, 2]")
        result = learn("scan", str(self.repo), "--no-gh")
        self.assertEqual(result.returncode, 2)
        self.assertIn("must be a JSON object", result.stderr)

    def test_lessons_next_number_and_concepts(self) -> None:
        write(
            self.repo / "learn" / "01-scaffold" / "TICKET.md",
            "---\nstatus: done\nkind: scaffold\n---\n",
        )
        write(
            self.repo / "learn" / "02-dropped" / "TICKET.md",
            "---\nstatus: dropped\nkind: endpoint\n---\n",
        )
        write(
            self.repo / "learn" / "03-register" / "TICKET.md",
            "---\r\nstatus: in-progress\r\nkind: endpoint\r\nbranch: feat/register\r\n---\r\n",
        )
        write(self.repo / "learn" / "notes" / "x.md", "x")
        write(self.repo / "learn" / "php-concepts.md", "# PHP\n\n## Readonly class\n\n## Enum\n")
        out = self.scan()
        self.assertIn("lesson 03-register: in-progress, endpoint\n", out)
        self.assertNotIn("01-scaffold", out)
        self.assertIn("lessons finished: 2\nnext lesson number: 04\nphp concepts seen: 2\n", out)

    def test_scan_changes_nothing(self) -> None:
        make_app(self.repo)
        self.init()
        self.commit()
        before = sorted(
            path.as_posix() for path in self.repo.rglob("*") if ".git/" not in path.as_posix()
        )
        self.scan()
        after = sorted(
            path.as_posix() for path in self.repo.rglob("*") if ".git/" not in path.as_posix()
        )
        self.assertEqual(before, after)

    def test_missing_repo_is_an_error(self) -> None:
        result = learn("scan", str(self.tmp / "nope"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("not a directory", result.stderr)


class Guide(Base):
    def guide(self, steps: int, padding: str = "") -> Path:
        text = "# Guide: x\n\n## The big idea\nIdea.\n\n"
        text += "".join(
            f"## Step {n}: title {n}\nWhat: thing {n}{padding}\n\n" for n in range(1, steps + 1)
        )
        path = self.tmp / "GUIDE.md"
        write(path, text + "## Finish\nGates.\n")
        return path

    def test_step_prints_only_that_step(self) -> None:
        out = learn("step", str(self.guide(3)), "2").stdout
        self.assertEqual(out, "## Step 2: title 2\nWhat: thing 2\n")

    def test_last_step_stops_before_the_finish_section(self) -> None:
        self.assertNotIn("Finish", learn("step", str(self.guide(3)), "3").stdout)

    def test_missing_step_says_how_many_exist(self) -> None:
        result = learn("step", str(self.guide(3)), "9")
        self.assertEqual(result.returncode, 1)
        self.assertIn("steps up to 3", result.stderr)

    def test_size_within_limits_passes(self) -> None:
        result = learn("guide-size", str(self.guide(6)))
        self.assertEqual(result.returncode, 0)
        self.assertIn("steps: 6/6", result.stdout)

    def test_size_limits_fail(self) -> None:
        self.assertEqual(learn("guide-size", str(self.guide(7))).returncode, 1)
        result = learn("guide-size", str(self.guide(2, padding="x" * 15000)))
        self.assertEqual(result.returncode, 1)
        self.assertIn("over limit", result.stdout)

    def test_missing_guide_and_bad_usage(self) -> None:
        self.assertEqual(learn("step", str(self.tmp / "nope.md"), "1").returncode, 2)
        self.assertEqual(learn("step", str(self.guide(1)), "one").returncode, 2)
        self.assertEqual(learn("explode").returncode, 2)


class Cleanup(Base):
    def prepared(self, status: str = "done") -> Path:
        self.init()
        write(self.repo / "a.txt", "a")
        write(self.repo / ".gitignore", "learn/\n")
        self.commit()
        path = self.tmp / "repo-lessons" / "01-x"
        git(self.repo, "worktree", "add", "-q", "--detach", str(path), "HEAD")
        write(
            self.repo / "learn" / "01-x" / "TICKET.md",
            f"---\nstatus: {status}\nkind: endpoint\nbranch: feat/x\n---\n",
        )
        write(self.repo / "learn" / "01-x" / "README.md", f"# L\n\n- Worktree: {path}\n")
        return path

    def stub_gh(self, code: int, output: str) -> dict[str, str]:
        stub = self.tmp / "gh-stub.php"
        write(stub, f"<?php\necho {json.dumps(output)};\nexit({code});\n")
        return {"LEARN_GH": str(stub)}

    def test_unknown_merge_state_keeps_the_worktree(self) -> None:
        path = self.prepared()
        out = learn("cleanup", str(self.repo), "--no-gh").stdout
        self.assertIn("keep 01-x: merge state unknown", out)
        self.assertTrue(path.exists())

    def test_merged_pr_removes_the_worktree(self) -> None:
        path = self.prepared()
        out = learn("cleanup", str(self.repo), env=self.stub_gh(0, '[{"number": 7}]')).stdout
        self.assertIn("removed ", out)
        self.assertFalse(path.exists())
        self.assertIn("removed empty", out)
        self.assertFalse(path.parent.exists())

    def test_unmerged_pr_keeps_the_worktree(self) -> None:
        path = self.prepared()
        out = learn("cleanup", str(self.repo), env=self.stub_gh(0, "[]")).stdout
        self.assertIn("keep 01-x: no merged PR", out)
        self.assertTrue(path.exists())

    def test_gh_failure_or_bad_output_keeps_the_worktree(self) -> None:
        path = self.prepared()
        for stub in (self.stub_gh(1, "not logged in"), self.stub_gh(0, "<html>")):
            out = learn("cleanup", str(self.repo), env=stub).stdout
            self.assertIn("merge state unknown", out)
            self.assertTrue(path.exists())

    def test_scan_reports_a_merged_lesson_still_in_progress(self) -> None:
        self.prepared(status="in-progress")
        out = learn("scan", str(self.repo), env=self.stub_gh(0, '[{"number": 7}]')).stdout
        self.assertIn("lesson 01-x: in-progress, endpoint, merged PR #7", out)

    def test_abandoned_removes_worktree_but_keeps_docs(self) -> None:
        path = self.prepared()
        result = learn("cleanup", str(self.repo), "--abandoned", "01-x", "--no-gh")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertFalse(path.exists())
        self.assertTrue((self.repo / "learn" / "01-x" / "TICKET.md").exists())

    def test_dry_run_removes_nothing(self) -> None:
        path = self.prepared()
        out = learn("cleanup", str(self.repo), "--abandoned", "01-x", "--dry-run", "--no-gh").stdout
        self.assertIn("would remove", out)
        self.assertTrue(path.exists())

    def test_never_removes_paths_that_are_not_its_worktree(self) -> None:
        self.prepared()
        outside = self.tmp / "precious"
        write(outside / "keep.txt", "keep")
        write(
            self.repo / "learn" / "02-y" / "TICKET.md", "---\nstatus: done\nbranch: feat/y\n---\n"
        )
        write(self.repo / "learn" / "02-y" / "README.md", f"- Worktree: {outside}\n")
        write(self.repo / "learn" / "03-z" / "README.md", f"- Worktree: {self.repo / 'learn'}\n")
        out = learn("cleanup", str(self.repo), "--abandoned", "02-y", "--no-gh").stdout
        self.assertIn("keep 02-y:", out)
        self.assertIn("not a registered worktree", out)
        self.assertIn("keep 03-z: recorded path is inside the repo", out)
        self.assertTrue((outside / "keep.txt").exists())

    def test_unknown_abandoned_name_is_an_error(self) -> None:
        self.prepared()
        result = learn("cleanup", str(self.repo), "--abandoned", "99-nope", "--no-gh")
        self.assertEqual(result.returncode, 2)
        self.assertIn("no lesson named 99-nope", result.stderr)


class Docs(unittest.TestCase):
    def setUp(self) -> None:
        self.check = (SKILL / "references" / "check.md").read_text(encoding="utf-8")
        table = self.check.split("## Rules", 1)[1].split("## Checks", 1)[0]
        rows = [
            row.split("|")
            for row in table.splitlines()
            if row.startswith("| ") and "---" not in row
        ][1:]
        self.boost = {
            name
            for row in rows
            for name in re.findall(r"[a-z][a-z-]+", row[2])
            if "`" not in row[2]
        }
        self.api = {
            name
            for row in rows
            for name in re.findall(r"\b[a-z]+-[a-z-]+\b", row[3])
            if "`" not in row[3]
        }

    def test_every_boost_rule_named_in_check_exists(self) -> None:
        self.assertTrue(self.boost)
        self.assertEqual(self.boost - BOOST_RULES - {"none"}, set())

    def test_every_api_rule_named_in_check_exists(self) -> None:
        self.assertEqual(self.api - {path.stem for path in API_RULES.glob("*.md")}, set())

    def test_every_api_rule_is_reachable_from_check(self) -> None:
        self.assertEqual({path.stem for path in API_RULES.glob("*.md")} - self.api, set())

    def test_relative_links_resolve(self) -> None:
        for path in [SKILL / "SKILL.md", *sorted((SKILL / "references").glob("*.md"))]:
            for target in re.findall(
                r"\]\(([^)#]+\.(?:md|php))\)", path.read_text(encoding="utf-8")
            ):
                with self.subTest(f"{path.name} -> {target}"):
                    self.assertTrue((path.parent / target).is_file())

    def test_every_reference_is_routed_from_the_skill(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for path in (SKILL / "references").glob("*.md"):
            self.assertIn(f"references/{path.name}", text)

    def test_other_stacks_stay_out(self) -> None:
        for path in [SKILL / "SKILL.md", *(SKILL / "references").glob("*.md")]:
            text = path.read_text(encoding="utf-8").lower()
            for word in ("fastapi", "python", "pytest", "nestjs", "uv run"):
                self.assertNotIn(word, text, f"{path.name} mentions {word}")


if __name__ == "__main__":
    unittest.main()
