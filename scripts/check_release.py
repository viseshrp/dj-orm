#!/usr/bin/env python3
"""Validate Djorm release provenance, version, and repository state."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re
import subprocess

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib


RELEASE_RE = re.compile(r"^(?P<upstream>\d+\.\d+\.\d+)\.(?P<revision>\d+)$")


def read_toml(path: Path) -> dict:
    with path.open("rb") as toml_file:
        return tomllib.load(toml_file)


def read_distribution_version(root: Path) -> str:
    version_text = (root / "djorm" / "_version.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']$', version_text, re.MULTILINE)
    if match is None:
        raise ValueError("djorm/_version.py does not define one literal __version__ value")
    return match.group(1)


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()


def validate(root: Path, tag: str) -> list[str]:
    errors: list[str] = []
    project = read_toml(root / "pyproject.toml")
    maintenance = read_toml(root / ".djorm-maintenance.toml")
    version = read_distribution_version(root)
    match = RELEASE_RE.fullmatch(version)

    if project["project"]["name"] != "dj-orm":
        errors.append("pyproject.toml must publish the dj-orm distribution")
    if maintenance.get("distribution") != "dj-orm":
        errors.append("maintenance metadata must name the dj-orm distribution")
    if tag != f"v{version}":
        errors.append(f"tag {tag!r} does not match package version {version!r}")
    if match is None:
        errors.append("package version must contain Django A.B.C plus a Djorm revision")
    else:
        recorded_ref = str(maintenance.get("upstream_ref", ""))
        upstream_parts = match.group("upstream")
        recorded_parts = [int(part) for part in recorded_ref.split(".")] if recorded_ref else []
        recorded_parts.extend([0] * (3 - len(recorded_parts)))
        recorded_normalized = ".".join(str(part) for part in recorded_parts[:3])
        if recorded_normalized != upstream_parts:
            errors.append(
                f"package version maps to Django {upstream_parts}, "
                f"but provenance records {recorded_ref}"
            )
        if int(match.group("revision")) != int(maintenance.get("release_revision", -1)):
            errors.append("package revision does not match maintenance metadata")

    if (root / "django").exists():
        errors.append("a top-level django package is present")
    if git(root, "status", "--porcelain"):
        errors.append("working tree is not clean")

    changelog_line = f"## [{version}] - {date.today().isoformat()}"
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    if changelog_line not in changelog.splitlines():
        errors.append(f"CHANGELOG.md must contain: {changelog_line}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    errors = validate(root, args.tag)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Release checks passed for {args.tag}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
