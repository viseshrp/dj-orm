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


FINAL_TAG_RE = re.compile(r"^\d+(?:\.\d+){0,2}$")
SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\."
    r"(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)$"
)


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


def release_series(django_ref: str) -> str | None:
    if FINAL_TAG_RE.fullmatch(django_ref) is None:
        return None
    parts = django_ref.split(".")
    return ".".join(parts[:2]) if len(parts) > 1 else parts[0]


def read_lts_version_majors(maintenance: dict) -> dict[str, int] | None:
    mapping = maintenance.get("lts_version_majors")
    if not isinstance(mapping, dict) or not mapping:
        return None
    if not all(
        isinstance(series, str)
        and isinstance(major, int)
        and not isinstance(major, bool)
        and major >= 0
        for series, major in mapping.items()
    ):
        return None
    if list(mapping.values()) != list(range(len(mapping))):
        return None
    return mapping


def validate(root: Path, tag: str) -> list[str]:
    errors: list[str] = []
    project = read_toml(root / "pyproject.toml")
    maintenance = read_toml(root / ".djorm-maintenance.toml")
    version = read_distribution_version(root)
    match = SEMVER_RE.fullmatch(version)

    if project["project"]["name"] != "dj-orm":
        errors.append("pyproject.toml must publish the dj-orm distribution")
    if maintenance.get("distribution") != "dj-orm":
        errors.append("maintenance metadata must name the dj-orm distribution")
    if maintenance.get("schema") != 3:
        errors.append("maintenance metadata must use schema 3")
    if tag != f"v{version}":
        errors.append(f"tag {tag!r} does not match package version {version!r}")
    if match is None:
        errors.append("package version must be semantic version X.Y.Z")
    else:
        recorded_ref = str(maintenance.get("upstream_ref", ""))
        recorded_series = release_series(recorded_ref)
        configured_series = maintenance.get("upstream_series")
        version_majors = read_lts_version_majors(maintenance)
        if recorded_series is None:
            errors.append("maintenance metadata must record a final numeric Django tag")
        elif configured_series != recorded_series:
            errors.append("upstream_series does not match the recorded Django tag")
        if version_majors is None:
            errors.append("maintenance metadata must define contiguous LTS SemVer majors")
        elif recorded_series not in version_majors:
            errors.append(f"Django {recorded_series} has no configured SemVer major")
        elif int(match.group("major")) != version_majors[recorded_series]:
            errors.append(
                f"package major does not map to the recorded Django {recorded_series} LTS"
            )
        if maintenance.get("release_version") != version:
            errors.append("package version does not match maintenance metadata")

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
