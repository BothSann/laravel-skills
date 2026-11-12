"""Behaviour of review.php and the laravel-review docs. Run: python -m unittest discover -s tests

Needs `php` on PATH, or its path in the PHP environment variable, and Git. The real `gh` is never
run: REVIEW_GH names a stand-in that answers from a JSON file and records what would be posted.
"""

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).parents[1]
SKILL = REPO / "skills" / "laravel-review"
SCRIPT = SKILL / "scripts" / "review.php"
API_RULES = REPO / "skills" / "laravel-api-practices" / "rules"
PHP = os.environ.get("PHP", "php")
ME = "reviewer"
HEAD = "a" * 40
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
STUB = r"""<?php
$state = json_decode(file_get_contents(getenv('REVIEW_STUB')), true);
$args = array_slice($argv, 1);
$line = implode(' ', $args);
if (isset($state['fail']) && str_contains($line, $state['fail'])) {
    fwrite(STDERR, 'HTTP 500');
    exit(1);
}
if ($line === 'api user --jq .login') {
    echo $state['user'];
} elseif (str_starts_with($line, 'pr view')) {
    echo json_encode($state['pr']);
} elseif (str_starts_with($line, 'pr diff')) {
    echo $state['diff'];
} elseif (str_contains($line, '--method POST')) {
    $file = $args[array_search('--input', $args) + 1];
    file_put_contents(getenv('REVIEW_STUB').'.posted', file_get_contents($file)."\n", FILE_APPEND);
} elseif (str_contains($line, '/reviews')) {
    echo json_encode([$state['reviews']]);
} elseif (str_starts_with($line, 'api graphql')) {
    $threads = ['reviewThreads' => ['nodes' => $state['threads']]];
    echo json_encode(['data' => ['repository' => ['pullRequest' => $threads]]]);
} else {
    fwrite(STDERR, "unexpected gh call: $line");
    exit(9);
}
"""
DIFF = """diff --git a/app/Services/PostService.php b/app/Services/PostService.php
index 1111111..2222222 100644
--- a/app/Services/PostService.php
+++ b/app/Services/PostService.php
@@ -10,6 +10,7 @@ class PostService
     public function create(array $data): Post
     {
-        return Post::create($data);
+        $post = Post::create($data);
+        return $post;
     }
 }
diff --git a/app/Old.php b/app/Old.php
deleted file mode 100644
--- a/app/Old.php
+++ /dev/null
@@ -1,2 +0,0 @@
-<?php
-class Old {}
diff --git a/app/Enums/Method.php b/app/Enums/Method.php
new file mode 100644
--- /dev/null
+++ b/app/Enums/Method.php
@@ -0,0 +1,3 @@
+<?php
+enum Method: string {}
+
\\ No newline at end of file
"""


def thread(
    path: str, body: str, *, author: str = ME, resolved: bool = False, line: int | None = 5
) -> dict:
    return {
        "isResolved": resolved,
        "path": path,
        "line": line,
        "originalLine": 3,
        "comments": {"nodes": [{"author": {"login": author}, "body": body}]},
    }


def finding(
    severity: str = "P2", title: str = "Wrap the writes in a transaction", **fields: object
) -> dict:
    base = {
        "severity": severity,
        "title": title,
        "body": "Because.",
        "path": "app/Services/PostService.php",
        "line": 12,
    }
    return {**base, **fields}


class Base(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(folder.cleanup)
        self.tmp = Path(folder.name).resolve()
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        (self.tmp / "gh.php").write_bytes(STUB.encode())
        self.state: dict[str, object] = {
            "user": ME,
            "pr": {
                "number": 12,
                "state": "OPEN",
                "headRefOid": HEAD,
                "headRefName": "feat/x",
                "baseRefName": "main",
                "url": "https://github.com/acme/api/pull/12",
            },
            "reviews": [],
            "threads": [],
            "diff": DIFF,
        }

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        stub = self.tmp / "state.json"
        stub.write_bytes(json.dumps(self.state).encode())
        env = {**os.environ, "REVIEW_GH": str(self.tmp / "gh.php"), "REVIEW_STUB": str(stub)}
        return subprocess.run(
            [PHP, str(SCRIPT), *args],
            capture_output=True,
            text=True,
            check=False,
            cwd=self.repo,
            env=env,
        )

    def posted(self) -> list[dict]:
        log = self.tmp / "state.json.posted"
        if not log.exists():
            return []
        return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]

    def findings(self, *items: object) -> str:
        path = self.tmp / "findings.json"
        path.write_bytes(json.dumps(list(items)).encode())
        return str(path)

    def git(self, *args: str) -> str:
        identity = [
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@example.com",
            "-c",
            "commit.gpgsign=false",
        ]
        done = subprocess.run(
            ["git", *identity, *args], cwd=self.repo, check=True, capture_output=True, text=True
        )
        return done.stdout.strip()


class Context(Base):
    def test_first_review_covers_the_whole_pull_request(self) -> None:
        out = self.run_script("context", "12").stdout
        self.assertIn("pr: #12 feat/x -> main, open, head aaaaaaa\n", out)
        self.assertIn("reviewer: reviewer\nlast review: none\nreview: the whole pull request", out)

    def test_changed_files_are_counted_and_deleted_files_left_out(self) -> None:
        out = self.run_script("context", "12").stdout
        self.assertIn("changed files: 2\n", out)
        self.assertIn("  app/Services/PostService.php (+2 -1)\n", out)
        self.assertIn("  app/Enums/Method.php (+3 -0)\n", out)
        self.assertNotIn("Old.php", out)

    def test_no_new_commits_since_the_last_review(self) -> None:
        self.state["reviews"] = [
            {"user": {"login": "someone"}, "commit_id": "b" * 40, "body": ""},
            {"user": {"login": ME}, "commit_id": HEAD, "body": ""},
        ]
        self.assertIn(
            "review: nothing new since your last review", self.run_script("context", "12").stdout
        )

    def test_new_commits_after_the_last_review_are_the_range(self) -> None:
        self.git("init", "-q", "-b", "main")
        (self.repo / "a.txt").write_text("a")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "one")
        first = self.git("rev-parse", "HEAD")
        (self.repo / "a.txt").write_text("b")
        self.git("commit", "-q", "-am", "two")
        head = self.git("rev-parse", "HEAD")
        self.state["pr"]["headRefOid"] = head  # type: ignore[index]
        self.state["reviews"] = [{"user": {"login": ME}, "commit_id": first, "body": ""}]
        out = self.run_script("context", "12").stdout
        self.assertIn(f"review: only new commits (git diff {first}..{head})", out)

    def test_a_rewritten_branch_is_reviewed_in_full(self) -> None:
        self.git("init", "-q", "-b", "main")
        self.state["reviews"] = [{"user": {"login": ME}, "commit_id": "c" * 40, "body": ""}]
        out = self.run_script("context", "12").stdout
        self.assertIn("(rewritten or not fetched)\nreview: the whole pull request", out)

    def test_lists_only_the_reviewers_unresolved_threads(self) -> None:
        self.state["threads"] = [
            thread("app/A.php", "**P1 — Check the result.** Body text."),
            thread("app/B.php", "**P2 — Someone else's.** Body.", author="other"),
            thread("app/C.php", "**P2 — Already resolved.** Body.", resolved=True),
            thread("app/D.php", "Plain comment without a heading\nsecond line", line=None),
        ]
        out = self.run_script("context", "12").stdout
        self.assertIn("your open threads: 2\n", out)
        self.assertIn("  app/A.php:5 P1 — Check the result\n", out)
        self.assertIn("  app/D.php:3 Plain comment without a heading\n", out)
        self.assertNotIn("app/B.php", out)
        self.assertNotIn("app/C.php", out)

    def test_layers_rule_sources_and_missing_boost(self) -> None:
        out = self.run_script("context", "12").stdout
        self.assertIn("layers: none\nwarning: Laravel Boost is not installed", out)
        self.assertIn("rule sources: none", out)
        (self.repo / "composer.json").write_text(
            json.dumps(
                {
                    "require": {"nwidart/laravel-modules": "^13"},
                    "require-dev": {"laravel/boost": "^2"},
                }
            )
        )
        (self.repo / "AGENTS.md").write_text("rules")
        (self.repo / ".ai" / "rules").mkdir(parents=True)
        out = self.run_script("context", "12").stdout
        self.assertIn("layers: boost, modules\nrule sources: AGENTS.md, .ai/rules\n", out)
        self.assertNotIn("warning", out)

    def test_bad_number_and_gh_failure_stop(self) -> None:
        result = self.run_script("context", "twelve")
        self.assertEqual(result.returncode, 2)
        self.assertIn("is not a pull request number", result.stderr)
        self.state["fail"] = "pr view"
        result = self.run_script("context", "12")
        self.assertEqual(result.returncode, 2)
        self.assertIn("gh pr view 12 failed: HTTP 500", result.stderr)

    def test_usage(self) -> None:
        self.assertEqual(self.run_script().returncode, 2)
        self.assertEqual(self.run_script("post", "12").returncode, 2)


class Post(Base):
    def test_preview_prints_the_comment_and_posts_nothing(self) -> None:
        result = self.run_script("preview", "12", self.findings(finding(title="Wrap the writes.")))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "app/Services/PostService.php:12\n  **P2 — Wrap the writes.** Because.\n", result.stdout
        )
        self.assertIn(
            "preview only, nothing posted (1 inline, 0 outside the changed lines, 0 skipped)",
            result.stdout,
        )
        self.assertEqual(self.posted(), [])

    def test_post_sends_one_comment_review_at_the_head_commit(self) -> None:
        items = [
            finding(
                "P3", "Use TitleCase cases", path="app/Enums/Method.php", line=2, source="AGENTS.md"
            ),
            finding("P1", "Check the result", line=13),
            finding("P2", "Add a test", line=10),
        ]
        result = self.run_script("post", "12", self.findings(*items))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("posted one review on #12 at aaaaaaa (3 inline, 0 outside", result.stdout)
        (payload,) = self.posted()
        self.assertEqual(payload["commit_id"], HEAD)
        self.assertEqual(payload["event"], "COMMENT")
        self.assertEqual(payload["body"], "")
        self.assertEqual(
            [(c["path"], c["line"], c["side"]) for c in payload["comments"]],
            [
                ("app/Services/PostService.php", 13, "RIGHT"),
                ("app/Services/PostService.php", 10, "RIGHT"),
                ("app/Enums/Method.php", 2, "RIGHT"),
            ],
        )
        self.assertEqual(payload["comments"][0]["body"], "**P1 — Check the result.** Because.")

    def test_lines_the_pull_request_does_not_show_go_in_the_body(self) -> None:
        items = [
            finding(title="Far from the change", line=200),
            finding(title="Untouched file", path="app/Models/Post.php", line=4),
            finding(title="Deleted file", path="app/Old.php", line=1),
        ]
        self.run_script("post", "12", self.findings(*items))
        (payload,) = self.posted()
        self.assertEqual(payload["comments"], [])
        self.assertTrue(
            payload["body"].startswith("Findings on lines this pull request does not change:")
        )
        self.assertIn(
            "- `app/Services/PostService.php:200` **P2 — Far from the change.** Because.",
            payload["body"],
        )
        self.assertIn("`app/Models/Post.php:4`", payload["body"])
        self.assertIn("`app/Old.php:1`", payload["body"])

    def test_a_finding_with_an_open_thread_is_skipped(self) -> None:
        self.state["threads"] = [
            thread(
                "app/Services/PostService.php",
                "**P2 — Wrap the writes in a transaction.** Old text.",
            ),
            thread("app/Enums/Method.php", "**P2 — Add a test.** Other file."),
            thread(
                "app/Services/PostService.php", "**P1 — Check the result.** Fixed.", resolved=True
            ),
        ]
        items = [
            finding(title="wrap the Writes in a transaction"),
            finding(title="Add a test", line=10),
            finding("P1", "Check the result", line=13),
        ]
        result = self.run_script("post", "12", self.findings(*items))
        self.assertIn(
            "skipped, already has an open thread: app/Services/PostService.php", result.stdout
        )
        (payload,) = self.posted()
        self.assertEqual(
            [c["body"].split(".**")[0] for c in payload["comments"]],
            ["**P1 — Check the result", "**P2 — Add a test"],
        )

    def test_nothing_new_posts_nothing(self) -> None:
        self.state["threads"] = [
            thread("app/Services/PostService.php", "**P2 — Wrap the writes in a transaction.** x")
        ]
        result = self.run_script("post", "12", self.findings(finding()))
        self.assertEqual(result.returncode, 0)
        self.assertIn("nothing new to post", result.stdout)
        self.assertEqual(self.posted(), [])

    def test_invalid_findings_are_refused_before_posting(self) -> None:
        items = [
            finding("P4"),
            finding("P3", "No source"),
            finding(title=""),
            finding(line=0),
            "not an object",
        ]
        result = self.run_script("post", "12", self.findings(*items))
        self.assertEqual(result.returncode, 2)
        for message in (
            "finding 1: severity must be P1, P2 or P3",
            'finding 2: a P3 needs "source"',
            "finding 3: title, body and path are required",
            "finding 4: line must be a positive number",
            "finding 5: must be an object",
        ):
            self.assertIn(message, result.stderr)
        self.assertEqual(self.posted(), [])

    def test_a_file_that_is_not_a_list_is_refused(self) -> None:
        path = self.tmp / "bad.json"
        path.write_text('{"severity": "P1"}')
        self.assertEqual(self.run_script("post", "12", str(path)).returncode, 2)
        self.assertEqual(
            self.run_script("post", "12", str(self.tmp / "missing.json")).returncode, 2
        )

    def test_a_failed_post_is_reported(self) -> None:
        self.state["fail"] = "--method POST"
        result = self.run_script("post", "12", self.findings(finding()))
        self.assertEqual(result.returncode, 2)
        self.assertIn("failed: HTTP 500", result.stderr)
        self.assertNotIn("posted one review", result.stdout)


class Clean(Base):
    def test_posts_one_marked_comment(self) -> None:
        result = self.run_script("clean", "12")
        self.assertEqual(result.returncode, 0, result.stderr)
        (payload,) = self.posted()
        self.assertEqual(payload["event"], "COMMENT")
        self.assertEqual(payload["comments"], [])
        self.assertIn(
            "**No issues found** at `aaaaaaa`. Ready to merge once a person approves.",
            payload["body"],
        )
        self.assertIn("<!-- laravel-review:clean -->", payload["body"])

    def test_is_not_repeated_for_the_same_commit(self) -> None:
        self.state["reviews"] = [
            {
                "user": {"login": ME},
                "commit_id": HEAD,
                "body": "ok\n\n<!-- laravel-review:clean -->",
            }
        ]
        result = self.run_script("clean", "12")
        self.assertIn("already posted for aaaaaaa", result.stdout)
        self.assertEqual(self.posted(), [])

    def test_is_posted_again_after_new_commits(self) -> None:
        self.state["reviews"] = [
            {"user": {"login": ME}, "commit_id": "b" * 40, "body": "<!-- laravel-review:clean -->"}
        ]
        self.run_script("clean", "12")
        self.assertEqual(len(self.posted()), 1)

    def test_mentions_threads_still_open(self) -> None:
        self.state["threads"] = [thread("app/A.php", "**P3 — Rename it.** x")]
        self.run_script("clean", "12")
        self.assertIn(
            "1 earlier thread is still open for the author to resolve.", self.posted()[0]["body"]
        )


class Docs(unittest.TestCase):
    def setUp(self) -> None:
        method = (SKILL / "references" / "method.md").read_text(encoding="utf-8")
        table = method.split("| Diff touches |", 1)[1].split("\n\n", 1)[0]
        rows = [row.split("|") for row in table.splitlines() if row.startswith("| ")]
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

    def test_every_boost_rule_named_exists(self) -> None:
        self.assertTrue(self.boost)
        self.assertEqual(self.boost - BOOST_RULES - {"none"}, set())

    def test_every_api_rule_is_named_and_exists(self) -> None:
        self.assertEqual(self.api, {path.stem for path in API_RULES.glob("*.md")})

    def test_relative_links_resolve(self) -> None:
        for path in [SKILL / "SKILL.md", *sorted((SKILL / "references").glob("*.md"))]:
            for target in re.findall(
                r"\]\(([^)#]+\.(?:md|php))\)", path.read_text(encoding="utf-8")
            ):
                with self.subTest(f"{path.name} -> {target}"):
                    self.assertTrue((path.parent / target).is_file())

    def test_the_script_can_only_comment(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("APPROVE", source)
        self.assertNotIn("REQUEST_CHANGES", source)
        self.assertEqual(set(re.findall(r"'event' => '(\w+)'", source)), {"COMMENT"})

    def test_the_example_finding_is_valid_json(self) -> None:
        text = (SKILL / "references" / "findings.md").read_text(encoding="utf-8")
        (block,) = re.findall(r"```json\n(.*?)```", text, re.S)
        self.assertEqual(json.loads(block)[0]["severity"], "P3")


if __name__ == "__main__":
    unittest.main()
