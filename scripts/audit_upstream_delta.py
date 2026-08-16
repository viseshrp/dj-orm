#!/usr/bin/env python3
"""Audit the maintained djrm delta against its exact Django source tag."""

from __future__ import annotations

import argparse
import ast
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib


BASELINE_NAME = ".djrm-upstream-delta.toml"
CONFIG_NAME = ".djrm-maintenance.toml"
SCOPES = ("djrm", "tests")


class DeltaAuditError(RuntimeError):
    """The maintained delta differs from its reviewed baseline."""


@dataclass(frozen=True)
class ScopeReport:
    common: int
    byte_differences: int
    raw_ast_differences: tuple[str, ...]
    executable_ast_differences: tuple[str, ...]
    non_ast_byte_differences: int
    upstream_only: int
    upstream_only_sha256: str
    fork_only: int
    fork_only_sha256: str


class StripDocstrings(ast.NodeTransformer):
    """Remove docstrings before comparing executable syntax trees."""

    def _strip(self, node: Any) -> Any:
        self.generic_visit(node)
        body = getattr(node, "body", None)
        if (
            isinstance(body, list)
            and body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            node.body = body[1:]
        return node

    visit_Module = _strip
    visit_ClassDef = _strip
    visit_FunctionDef = _strip
    visit_AsyncFunctionDef = _strip


def run(
    args: list[str],
    *,
    cwd: Path,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
    )


def git(repo: Path, *args: str) -> str:
    return run(["git", *args], cwd=repo).stdout.strip()


def read_toml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise DeltaAuditError(f"Missing required file: {path}")
    with path.open("rb") as source:
        return tomllib.load(source)


def tracked_scope_paths(repo: Path, scope: str) -> set[str]:
    output = run(["git", "ls-files", "-z", "--", scope], cwd=repo).stdout
    return {path for path in output.split("\0") if path}


def physical_scope_paths(repo: Path, scope: str) -> set[str]:
    root = repo / scope
    if not root.is_dir():
        return set()
    return {path.relative_to(repo).as_posix() for path in root.rglob("*") if path.is_file()}


def syntax_dump(source: bytes, *, executable: bool) -> str | None:
    try:
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return None
    if executable:
        tree = StripDocstrings().visit(tree)
        ast.fix_missing_locations(tree)
    return ast.dump(tree, include_attributes=False)


def path_set_sha256(paths: set[str]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.encode())
        digest.update(b"\0")
    return digest.hexdigest()


def compare_scope(current: Path, upstream: Path, scope: str) -> ScopeReport:
    current_paths = tracked_scope_paths(current, scope)
    upstream_paths = physical_scope_paths(upstream, scope)
    common = current_paths & upstream_paths
    byte_differences: list[str] = []
    raw_ast_differences: list[str] = []
    executable_ast_differences: list[str] = []

    for path in sorted(common):
        current_bytes = (current / path).read_bytes()
        upstream_bytes = (upstream / path).read_bytes()
        if current_bytes == upstream_bytes:
            continue
        byte_differences.append(path)
        if not path.endswith(".py"):
            continue
        current_raw = syntax_dump(current_bytes, executable=False)
        upstream_raw = syntax_dump(upstream_bytes, executable=False)
        if current_raw != upstream_raw:
            raw_ast_differences.append(path)
        current_executable = syntax_dump(current_bytes, executable=True)
        upstream_executable = syntax_dump(upstream_bytes, executable=True)
        if current_executable != upstream_executable:
            executable_ast_differences.append(path)

    upstream_only = upstream_paths - current_paths
    fork_only = current_paths - upstream_paths
    return ScopeReport(
        common=len(common),
        byte_differences=len(byte_differences),
        raw_ast_differences=tuple(raw_ast_differences),
        executable_ast_differences=tuple(executable_ast_differences),
        non_ast_byte_differences=len(byte_differences) - len(raw_ast_differences),
        upstream_only=len(upstream_only),
        upstream_only_sha256=path_set_sha256(upstream_only),
        fork_only=len(fork_only),
        fork_only_sha256=path_set_sha256(fork_only),
    )


def create_normalized_upstream(repo: Path, commit: str) -> tuple[Path, Path]:
    temporary_root = Path(tempfile.mkdtemp(prefix="djrm-delta-audit-"))
    worktree = temporary_root / "upstream"
    try:
        run(["git", "worktree", "add", "--detach", str(worktree), commit], cwd=repo)
        run(
            [
                sys.executable,
                str(repo / "scripts" / "rename_namespace.py"),
                "--repo-root",
                str(worktree),
            ],
            cwd=repo,
        )
    except Exception:
        run(
            ["git", "worktree", "remove", "--force", str(worktree)],
            cwd=repo,
            check=False,
        )
        shutil.rmtree(temporary_root, ignore_errors=True)
        raise
    return temporary_root, worktree


def collect_report(repo: Path) -> dict[str, Any]:
    config = read_toml(repo / CONFIG_NAME)
    upstream_ref = str(config["upstream_ref"])
    upstream_commit = str(config["upstream_base_commit"])
    resolved_commit = git(repo, "rev-parse", f"{upstream_commit}^{{commit}}")
    temporary_root, upstream = create_normalized_upstream(repo, resolved_commit)
    try:
        return {
            "upstream_ref": upstream_ref,
            "upstream_commit": resolved_commit,
            "djrm": asdict(compare_scope(repo, upstream, "djrm")),
            "tests": asdict(compare_scope(repo, upstream, "tests")),
        }
    finally:
        run(
            ["git", "worktree", "remove", "--force", str(upstream)],
            cwd=repo,
            check=False,
        )
        shutil.rmtree(temporary_root, ignore_errors=True)


def toml_string(value: str) -> str:
    return json.dumps(value)


def baseline_text(report: dict[str, Any]) -> str:
    lines = [
        "schema = 1",
        f"upstream_ref = {toml_string(report['upstream_ref'])}",
        f"upstream_commit = {toml_string(report['upstream_commit'])}",
    ]
    for scope in SCOPES:
        data = report[scope]
        lines.extend(
            [
                "",
                f"[{scope}]",
                f"max_byte_differences = {data['byte_differences']}",
                f"max_raw_ast_differences = {len(data['raw_ast_differences'])}",
                f"max_non_ast_byte_differences = {data['non_ast_byte_differences']}",
                f"upstream_only = {data['upstream_only']}",
                f"upstream_only_sha256 = {toml_string(data['upstream_only_sha256'])}",
                f"fork_only = {data['fork_only']}",
                f"fork_only_sha256 = {toml_string(data['fork_only_sha256'])}",
                "executable_ast_differences = [",
            ]
        )
        lines.extend(f"  {toml_string(path)}," for path in data["executable_ast_differences"])
        lines.append("]")
    return "\n".join(lines) + "\n"


def validate_scope(
    scope: str,
    report: dict[str, Any],
    baseline: dict[str, Any],
) -> list[str]:
    failures = []
    actual = report[scope]
    expected = baseline[scope]
    limits = (
        ("byte_differences", "max_byte_differences"),
        ("raw_ast_differences", "max_raw_ast_differences"),
        ("non_ast_byte_differences", "max_non_ast_byte_differences"),
    )
    for actual_name, limit_name in limits:
        actual_value = actual[actual_name]
        if isinstance(actual_value, list | tuple):
            actual_value = len(actual_value)
        if actual_value > expected[limit_name]:
            failures.append(
                f"{scope} {actual_name} increased: {actual_value} > {expected[limit_name]}"
            )

    actual_executable = list(actual["executable_ast_differences"])
    if actual_executable != expected["executable_ast_differences"]:
        failures.append(f"{scope} executable AST allowlist changed")

    for name in (
        "upstream_only",
        "upstream_only_sha256",
        "fork_only",
        "fork_only_sha256",
    ):
        if actual[name] != expected[name]:
            failures.append(f"{scope} {name} changed: {actual[name]!r} != {expected[name]!r}")
    return failures


def validate_report(
    report: dict[str, Any],
    baseline: dict[str, Any],
) -> list[str]:
    failures = []
    if baseline.get("schema") != 1:
        failures.append(f"unsupported baseline schema: {baseline.get('schema')!r}")
    for name in ("upstream_ref", "upstream_commit"):
        if report[name] != baseline.get(name):
            failures.append(f"{name} changed: {report[name]!r} != {baseline.get(name)!r}")
    for scope in SCOPES:
        if scope not in baseline:
            failures.append(f"baseline is missing [{scope}]")
        else:
            failures.extend(validate_scope(scope, report, baseline))
    return failures


def summary(report: dict[str, Any]) -> str:
    lines = [f"Upstream delta: Django {report['upstream_ref']} ({report['upstream_commit'][:12]})"]
    for scope in SCOPES:
        data = report[scope]
        lines.append(
            f"{scope}: {data['byte_differences']} byte, "
            f"{len(data['raw_ast_differences'])} AST, "
            f"{len(data['executable_ast_differences'])} executable AST, "
            f"{data['non_ast_byte_differences']} non-AST differences"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Accept the current measured delta as the reviewed baseline.",
    )
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    try:
        report = collect_report(repo)
        if args.write_baseline:
            (repo / BASELINE_NAME).write_text(
                baseline_text(report),
                encoding="utf-8",
            )
            print(summary(report))
            print(f"Wrote reviewed baseline: {BASELINE_NAME}")
            return 0
        if args.json:
            print(json.dumps(report, indent=2))
            return 0
        baseline = read_toml(repo / BASELINE_NAME)
        failures = validate_report(report, baseline)
        print(summary(report))
        if failures:
            print("Delta baseline check failed:", file=sys.stderr)
            for failure in failures:
                print(f"  - {failure}", file=sys.stderr)
            print(
                "Review the report, then run with --write-baseline to accept it.",
                file=sys.stderr,
            )
            return 1
        print("Upstream delta matches the reviewed baseline.")
        return 0
    except (DeltaAuditError, KeyError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
