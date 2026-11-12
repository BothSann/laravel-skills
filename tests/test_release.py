"""The version check that guards releases. Run: python -m unittest discover tests"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).parents[1]
SCRIPT = REPO / "scripts" / "check_version.py"


def check(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False
    )


class RepoVersions(unittest.TestCase):
    def test_all_skills_share_one_version(self) -> None:
        result = check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ok: 2 skills", result.stdout)

    def test_a_wrong_tag_is_refused(self) -> None:
        result = check("v9.9.9")
        self.assertEqual(result.returncode, 1)
        self.assertIn("doesn't match", result.stderr)


class Fixtures(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)

    def skill(self, name: str, meta: str) -> None:
        path = self.root / "skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_bytes(f"---\nname: {name}\nmetadata:\n{meta}---\n# Body\n".encode())

    def run_check(self, *args: str) -> subprocess.CompletedProcess[str]:
        return check("--root", str(self.root), *args)

    def test_matching_tag_passes(self) -> None:
        self.skill("a", '  version: "1.2.3"\n')
        self.skill("b", '  version: "1.2.3"\r\n')
        self.assertEqual(self.run_check("v1.2.3").returncode, 0)

    def test_skills_that_disagree_are_refused(self) -> None:
        self.skill("a", '  version: "1.2.3"\n')
        self.skill("b", '  version: "1.2.4"\n')
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("skills disagree", result.stderr)

    def test_a_missing_version_is_refused(self) -> None:
        self.skill("a", '  version: "1.2.3"\n')
        self.skill("b", "  author: x\n")
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("b: no version", result.stderr)

    def test_no_skills_is_refused(self) -> None:
        self.assertEqual(self.run_check().returncode, 1)


if __name__ == "__main__":
    unittest.main()
