#!/usr/bin/env python3
"""Check that physical checkout paths match Git's tracked spelling."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
from typing import Any


def physical_paths(root: Path, tracked: set[str]) -> set[str]:
    tree: dict[str, Any] = {}
    for tracked_path in tracked:
        branch = tree
        for part in Path(tracked_path).parts:
            branch = branch.setdefault(part, {})

    paths: set[str] = set()
    pending: list[tuple[Path, dict[str, Any], tuple[str, ...]]] = [(root, tree, ())]
    while pending:
        directory, expected_entries, actual_parts = pending.pop()
        with os.scandir(directory) as entries:
            by_case = {entry.name.casefold(): entry for entry in entries}
        for expected_name, children in expected_entries.items():
            entry = by_case.get(expected_name.casefold())
            if entry is None:
                continue
            path_parts = (*actual_parts, entry.name)
            if children and entry.is_dir(follow_symlinks=False):
                pending.append((Path(entry.path), children, path_parts))
            else:
                paths.add(Path(*path_parts).as_posix())
    return paths


def case_mismatches(
    tracked: set[str],
    physical: set[str],
) -> list[tuple[str, tuple[str, ...]]]:
    physical_by_case: dict[str, list[str]] = {}
    for path in physical:
        physical_by_case.setdefault(path.casefold(), []).append(path)

    mismatches = []
    for path in sorted(tracked):
        if path in physical:
            continue
        alternatives = tuple(sorted(physical_by_case.get(path.casefold(), [])))
        if alternatives:
            mismatches.append((path, alternatives))
    return mismatches


def tracked_paths(root: Path) -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return {path.decode() for path in result.stdout.split(b"\0") if path}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args()
    root = args.repo_root.resolve()
    tracked = tracked_paths(root)
    mismatches = case_mismatches(tracked, physical_paths(root, tracked))
    if mismatches:
        print("Physical paths do not match Git's tracked spelling:")
        for tracked, alternatives in mismatches:
            print(f"  tracked: {tracked}")
            print(f"  actual:  {', '.join(alternatives)}")
        return 1
    print("Physical path spelling matches the Git index.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
