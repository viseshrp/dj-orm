#!/usr/bin/env python3
"""Enforce path-specific djrm coverage baselines."""

from __future__ import annotations

import argparse
from io import StringIO
from pathlib import Path
import sys
from typing import Any

from coverage import Coverage
from coverage.exceptions import CoverageException

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib


def read_targets(root: Path) -> dict[str, Any]:
    with (root / "pyproject.toml").open("rb") as source:
        return tomllib.load(source)["tool"]["djrm"]["coverage"]


def measured_coverage(data_file: Path, include: list[str]) -> float:
    coverage = Coverage(data_file=str(data_file))
    coverage.load()
    output = StringIO()
    return coverage.report(
        include=include,
        file=output,
        skip_empty=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-file", required=True, type=Path)
    parser.add_argument("--target", required=True, choices=("modified", "fork"))
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args()
    root = args.repo_root.resolve()
    config = read_targets(root)
    floor = float(config[f"{args.target}_floor"])
    paths = list(config[f"{args.target}_paths"])
    try:
        measured = measured_coverage(
            args.data_file if args.data_file.is_absolute() else root / args.data_file,
            paths,
        )
    except CoverageException as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"{args.target} coverage: {measured:.2f}% (required: {floor:.2f}%)")
    if measured < floor:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
