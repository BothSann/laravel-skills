"""Structure checks for laravel-api-practices. Run: python -m unittest discover -s tests

The PHP example check needs `php` on PATH, or its path in the PHP environment variable.
"""

import os
import pathlib
import re
import subprocess
import tempfile
import unittest

SKILL = pathlib.Path(__file__).parents[1] / "skills" / "laravel-api-practices"
RULES = SKILL / "rules"
PHP = os.environ.get("PHP", "php")
ROW = re.compile(r"^\| .+ / [A-Z-]+[^|]* \| (\w+-) \| (.+) \|$", re.M)
PHP_BLOCK = re.compile(r"```php\n(.*?)```", re.S)
ARRAY_ITEM = re.compile(r"^(?://[^\n]*\n)*'[^']+' =>")


def indexed_rules() -> list[str]:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    return [
        prefix + name.strip() for prefix, names in ROW.findall(text) for name in names.split(",")
    ]


def as_php_file(block: str) -> str:
    """Wrap an example so PHP can parse it: array items become a returned array."""
    if ARRAY_ITEM.match(block):
        return f"<?php\nreturn [\n{block}];\n"
    return f"<?php\n{block}"


class RuleFiles(unittest.TestCase):
    def setUp(self) -> None:
        self.files = sorted(RULES.glob("*.md"))

    def test_index_matches_files_exactly(self) -> None:
        self.assertEqual(sorted(indexed_rules()), [f.stem for f in self.files])

    def test_stated_count_matches(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(f"{len(self.files)} rules;", text)

    def test_each_rule_has_title_impact_and_source(self) -> None:
        for path in self.files:
            with self.subTest(path.name):
                text = path.read_text(encoding="utf-8")
                self.assertTrue(text.startswith(f"# {path.stem}\n"))
                self.assertRegex(text, r"\*\*(CRITICAL|HIGH|MEDIUM-HIGH|MEDIUM)[,.]")
                self.assertRegex(text, r"(?m)^Source: https://\S+$")

    def test_impact_matches_the_index(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        by_prefix = {
            prefix: impact
            for impact, prefix in re.findall(r"^\| .+ / ([A-Z-]+) \| (\w+-) \|", text, re.M)
        }
        for path in self.files:
            with self.subTest(path.name):
                prefix = path.stem.split("-", 1)[0] + "-"
                self.assertIn(f"**{by_prefix[prefix]}.**", path.read_text(encoding="utf-8"))

    def test_php_examples_parse(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            for path in self.files:
                blocks = PHP_BLOCK.findall(path.read_text(encoding="utf-8"))
                self.assertTrue(blocks, f"{path.name} has no PHP example")
                for number, block in enumerate(blocks):
                    with self.subTest(f"{path.name} block {number}"):
                        example = pathlib.Path(folder) / f"{path.stem}-{number}.php"
                        example.write_bytes(as_php_file(block).encode())
                        result = subprocess.run(
                            [PHP, "-l", str(example)], capture_output=True, text=True, check=False
                        )
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
