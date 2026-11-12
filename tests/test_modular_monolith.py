"""Behaviour of boundaries.php. Run: python -m unittest discover -s tests

Needs `php` on PATH, or its path in the PHP environment variable. The Deptrac cases run the real
tool from tests/tools/vendor (`composer install --working-dir tests/tools`). Without it they are
skipped locally and fail in CI.
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).parents[1]
SCRIPT = REPO / "skills" / "laravel-modular-monolith" / "scripts" / "boundaries.php"
PHP = os.environ.get("PHP", "php")
DEPTRAC = REPO / "tests" / "tools" / "vendor" / "bin" / "deptrac"
EMPTY_REPORT = '{"Report": {"Violations": 0}, "files": {}}'


def php(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([PHP, *args], capture_output=True, text=True, check=False, cwd=root)


def run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return php(root, str(SCRIPT), *args)


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(data, indent=4) + "\n").encode())


def add_module(
    root: Path,
    name: str,
    *,
    uses: tuple[str, ...] = (),
    exposes: tuple[str, ...] = (),
    folder: str = "Modules",
    namespace: str | None = None,
) -> Path:
    module = root / folder / name
    namespace = namespace or f"Modules\\{name}\\"
    manifest: dict[str, object] = {"name": name, "alias": name.lower()}
    if uses or exposes:
        manifest["boundaries"] = {"uses": list(uses), "exposes": list(exposes)}
    write_json(module / "module.json", manifest)
    write_json(
        module / "composer.json",
        {
            "autoload": {
                "psr-4": {
                    namespace: "app/",
                    f"{namespace}Database\\Seeders\\": "database/seeders/",
                }
            }
        },
    )
    return module


def make_app(root: Path, folder: str = "Modules", host_app: bool = True) -> Path:
    (root / "artisan").write_bytes(b"#!/usr/bin/env php\n")
    write_json(
        root / "composer.json",
        {"extra": {"merge-plugin": {"include": [f"{folder}/*/composer.json"]}}},
    )
    if host_app:
        (root / "app").mkdir()
    return root


def php_class(path: Path, name: str, depends_on: str | None = None) -> None:
    namespace, _, short = name.rpartition("\\")
    body = f" public function run(\\{depends_on} $x): void {{}} " if depends_on else ""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(f"<?php\n\nnamespace {namespace};\n\nclass {short} {{{body}}}\n".encode())


def install_deptrac(root: Path, script: str | None = None) -> None:
    """Give the app a vendor/bin/deptrac: the real tool, or a stand-in script."""
    target = root / "vendor" / "bin" / "deptrac"
    target.parent.mkdir(parents=True, exist_ok=True)
    real = f"<?php\n\nrequire {json.dumps(DEPTRAC.as_posix())};\n"
    target.write_bytes((script or real).encode())


class Base(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(folder.cleanup)
        self.root = make_app(Path(folder.name).resolve())

    def config(self) -> str:
        return (self.root / "deptrac.yaml").read_bytes().decode()


class Inspect(Base):
    def test_lists_modules_with_their_dependencies(self) -> None:
        add_module(self.root, "Account")
        add_module(self.root, "Post", uses=("Account",))
        result = run(self.root, "inspect")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("modules: 2", result.stdout)
        self.assertIn("Post (Modules\\Post\\) uses: Account", result.stdout)
        self.assertIn("deptrac: missing", result.stdout)
        self.assertIn("deptrac.yaml: missing", result.stdout)
        self.assertFalse((self.root / "deptrac.yaml").exists())

    def test_reads_a_custom_folder_and_namespace_from_composer(self) -> None:
        folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(folder.cleanup)
        root = make_app(Path(folder.name).resolve(), folder="asgard")
        add_module(root, "Post", folder="asgard", namespace="Asgard\\Post\\")
        result = run(root, "inspect")
        self.assertIn("modules dir: asgard", result.stdout)
        self.assertIn("Post (Asgard\\Post\\)", result.stdout)

    def test_root_and_modules_options_override_detection(self) -> None:
        add_module(self.root, "Post", folder="packages")
        result = run(REPO, "inspect", "--root", str(self.root), "--modules", "packages")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("modules: 1", result.stdout)

    def test_refuses_unknown_self_and_cyclic_dependencies(self) -> None:
        add_module(self.root, "Account", uses=("Post",))
        add_module(self.root, "Post", uses=("Account", "Missing"))
        add_module(self.root, "Feed", uses=("Feed",))
        result = run(self.root, "inspect")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Post: boundaries.uses names unknown module Missing", result.stderr)
        self.assertIn("Feed: lists itself", result.stderr)
        self.assertIn("cycle: Account -> Post -> Account", result.stderr)

    def test_refuses_a_folder_that_is_not_a_laravel_app(self) -> None:
        (self.root / "artisan").unlink()
        result = run(self.root, "inspect")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no artisan file", result.stderr)

    def test_unknown_command_prints_usage(self) -> None:
        result = run(self.root, "explode")
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)


class Sync(Base):
    def test_writes_layers_and_rules_for_each_module(self) -> None:
        add_module(self.root, "Account", exposes=("Models\\User",))
        add_module(self.root, "Post", uses=("Account",))
        self.assertEqual(run(self.root, "sync").returncode, 0)
        config = self.config()
        self.assertIn("- './Modules'\n    - './app'\n", config)
        self.assertIn("value: '^Modules\\\\Post\\\\(?!(?:Contracts|Events)\\\\).+'", config)
        self.assertIn("value: '^Modules\\\\Account\\\\(?:Models\\\\User)$'", config)
        self.assertIn(
            "    Post:\n      - Post.Public\n      - Account.Public\n      - Account.Exposed\n"
            "      - App\n",
            config,
        )
        self.assertIn("    Post.Public:\n      - Account.Public\n", config)
        self.assertIn("    Account.Public: ~\n", config)
        self.assertIn("    App:\n      - Account.Public\n      - Account.Exposed\n", config)

    def test_leaves_out_the_host_app_when_there_is_none(self) -> None:
        (self.root / "app").rmdir()
        add_module(self.root, "Account")
        run(self.root, "sync")
        self.assertNotIn("App", self.config())

    def test_check_passes_until_the_modules_change(self) -> None:
        add_module(self.root, "Account")
        self.assertEqual(run(self.root, "sync", "--check").returncode, 1)
        run(self.root, "sync")
        self.assertEqual(run(self.root, "sync", "--check").returncode, 0)
        add_module(self.root, "Post")
        result = run(self.root, "sync", "--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("stale or missing", result.stderr)

    def test_check_accepts_windows_line_endings(self) -> None:
        add_module(self.root, "Account")
        run(self.root, "sync")
        path = self.root / "deptrac.yaml"
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        self.assertEqual(run(self.root, "sync", "--check").returncode, 0)

    def test_writes_nothing_while_there_are_errors(self) -> None:
        add_module(self.root, "Post", uses=("Missing",))
        self.assertEqual(run(self.root, "sync").returncode, 1)
        self.assertFalse((self.root / "deptrac.yaml").exists())


class SelftestWithoutDeptrac(Base):
    def test_needs_deptrac(self) -> None:
        add_module(self.root, "Account")
        result = run(self.root, "selftest")
        self.assertEqual(result.returncode, 1)
        self.assertIn("composer require --dev deptrac/deptrac", result.stderr)

    def test_needs_a_module(self) -> None:
        install_deptrac(self.root, "<?php\n")
        result = run(self.root, "selftest")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no modules found", result.stderr)

    def test_fails_when_the_tool_reports_nothing(self) -> None:
        """A stand-in Deptrac that finds no violations must not pass the self-test."""
        add_module(self.root, "Account")
        add_module(self.root, "Post", uses=("Account",))
        install_deptrac(
            self.root,
            "<?php\nforeach ($argv as $arg) {\n    if (str_starts_with($arg, '--output=')) {\n"
            f"        file_put_contents(substr($arg, 9), '{EMPTY_REPORT}');\n    }}\n}}\n",
        )
        result = run(self.root, "selftest")
        self.assertEqual(result.returncode, 1)
        self.assertIn("not caught: Modules\\Post\\Services\\SelftestCase", result.stderr)

    def test_fails_when_the_tool_gives_no_report(self) -> None:
        add_module(self.root, "Account")
        install_deptrac(self.root, "<?php\necho 'broken';\nexit(3);\n")
        result = run(self.root, "selftest")
        self.assertEqual(result.returncode, 1)
        self.assertIn("deptrac gave no report", result.stderr)
        self.assertIn("broken", result.stderr)


class WithDeptrac(Base):
    @classmethod
    def setUpClass(cls) -> None:
        if DEPTRAC.exists():
            return
        if os.environ.get("CI"):
            raise AssertionError(f"{DEPTRAC} is missing: run composer install in tests/tools")
        raise unittest.SkipTest("deptrac is not installed in tests/tools")

    def setUp(self) -> None:
        super().setUp()
        install_deptrac(self.root)

    def analyse(self) -> subprocess.CompletedProcess[str]:
        return php(
            self.root, "vendor/bin/deptrac", "analyse", "--no-cache", "--no-progress", "--no-ansi"
        )

    def test_selftest_passes_for_one_module(self) -> None:
        add_module(self.root, "Account")
        result = run(self.root, "selftest")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "ok: 2 planted violations caught, 2 allowed dependencies passed", result.stdout
        )

    def test_selftest_covers_uses_exposes_and_custom_namespaces(self) -> None:
        add_module(self.root, "Account", exposes=("Models\\User",), namespace="Acme\\Account\\")
        add_module(self.root, "Post", uses=("Account",))
        add_module(self.root, "Feed", uses=("Post",))
        result = run(self.root, "selftest")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "ok: 17 planted violations caught, 9 allowed dependencies passed", result.stdout
        )

    def test_selftest_leaves_the_app_untouched(self) -> None:
        add_module(self.root, "Account")
        before = sorted(path.as_posix() for path in self.root.rglob("*"))
        run(self.root, "selftest")
        self.assertEqual(before, sorted(path.as_posix() for path in self.root.rglob("*")))

    def test_real_code_fails_on_another_modules_model(self) -> None:
        add_module(self.root, "Account")
        post = add_module(self.root, "Post", uses=("Account",))
        php_class(
            self.root / "Modules/Account/app/Models/User.php", "Modules\\Account\\Models\\User"
        )
        php_class(
            post / "app/Services/PostService.php",
            "Modules\\Post\\Services\\PostService",
            "Modules\\Account\\Models\\User",
        )
        run(self.root, "sync")
        result = self.analyse()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(
            "PostService must not depend on Modules\\Account\\Models\\User", result.stdout
        )

    def test_real_code_passes_through_a_contract_and_ignores_tests(self) -> None:
        add_module(self.root, "Account")
        post = add_module(self.root, "Post", uses=("Account",))
        php_class(
            self.root / "Modules/Account/app/Models/User.php", "Modules\\Account\\Models\\User"
        )
        php_class(
            self.root / "Modules/Account/app/Contracts/AccountApi.php",
            "Modules\\Account\\Contracts\\AccountApi",
        )
        php_class(
            post / "app/Services/PostService.php",
            "Modules\\Post\\Services\\PostService",
            "Modules\\Account\\Contracts\\AccountApi",
        )
        php_class(
            post / "tests/Feature/PostTest.php",
            "Modules\\Post\\Tests\\Feature\\PostTest",
            "Modules\\Account\\Models\\User",
        )
        run(self.root, "sync")
        result = self.analyse()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_real_code_fails_when_the_dependency_is_not_declared(self) -> None:
        add_module(self.root, "Account")
        post = add_module(self.root, "Post")
        php_class(
            self.root / "Modules/Account/app/Contracts/AccountApi.php",
            "Modules\\Account\\Contracts\\AccountApi",
        )
        php_class(
            post / "app/Services/PostService.php",
            "Modules\\Post\\Services\\PostService",
            "Modules\\Account\\Contracts\\AccountApi",
        )
        run(self.root, "sync")
        self.assertEqual(self.analyse().returncode, 1)

    def test_host_app_may_use_only_public_code(self) -> None:
        add_module(self.root, "Account")
        php_class(
            self.root / "Modules/Account/app/Models/User.php", "Modules\\Account\\Models\\User"
        )
        php_class(
            self.root / "app/Console/Report.php",
            "App\\Console\\Report",
            "Modules\\Account\\Models\\User",
        )
        run(self.root, "sync")
        result = self.analyse()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("App\\Console\\Report must not depend on", result.stdout)


if __name__ == "__main__":
    unittest.main()
