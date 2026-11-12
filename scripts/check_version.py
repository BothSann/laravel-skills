#!/usr/bin/env python3
"""Check that all skills share one version, and that it matches a release tag if given."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

VERSION = re.compile(r'^\s+version:\s*"([^"]+)"\s*$', re.M)


def skill_versions(root: Path) -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for path in sorted((root / "skills").glob("*/SKILL.md")):
        match = VERSION.search(path.read_bytes().decode("utf-8-sig"))
        versions[path.parent.name] = match.group(1) if match else None
    return versions


def find_errors(versions: dict[str, str | None], tag: str | None) -> list[str]:
    if not versions:
        return ["no skills found"]
    errors = [f"{name}: no version" for name, version in versions.items() if version is None]
    found = {version for version in versions.values() if version is not None}
    if len(found) > 1:
        errors.append(f"skills disagree: {', '.join(sorted(found))}")
    if tag is not None and found != {tag.removeprefix("v")}:
        errors.append(
            f"tag {tag} doesn't match skill version: {', '.join(sorted(found)) or 'none'}"
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", nargs="?", help="release tag, such as v0.2.0")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    versions = skill_versions(args.root)
    errors = find_errors(versions, args.tag)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"ok: {len(versions)} skills at {next(iter(versions.values()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
