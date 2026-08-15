#!/usr/bin/env python3
"""Apply the Djorm fork commit stack to an exact Django LTS tag."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib


CONFIG_NAME = ".djorm-maintenance.toml"
STATE_NAME = "djorm-apply-state.json"
FINAL_TAG_RE = re.compile(r"^(?P<parts>\d+(?:\.\d+){0,2})$")


class ApplyError(RuntimeError):
    """A safe, actionable LTS application failure."""


@dataclass
class ApplyState:
    source_repo: str
    source_head: str
    output: str
    branch: str
    django_ref: str
    django_commit: str
    revision: int
    commits: list[str]
    namespace_commit: str
    next_index: int = 0
    generated_namespace_commit: str = ""


def run(
    args: list[str],
    *,
    cwd: Path,
    check: bool = True,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        check=check,
        text=True,
        capture_output=capture,
    )


def git(
    repo: Path,
    *args: str,
    check: bool = True,
    capture: bool = True,
) -> str:
    result = run(["git", *args], cwd=repo, check=check, capture=capture)
    return result.stdout.strip() if capture else ""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_config(source_repo: Path) -> dict[str, Any]:
    config_path = source_repo / CONFIG_NAME
    if not config_path.is_file():
        raise ApplyError(f"Missing maintenance configuration: {config_path}")
    with config_path.open("rb") as config_file:
        config = tomllib.load(config_file)
    if config.get("schema") != 1:
        raise ApplyError(f"Unsupported {CONFIG_NAME} schema: {config.get('schema')!r}")
    required = {
        "distribution",
        "yapc_commit",
        "upstream_remote",
        "upstream_url",
        "upstream_base_commit",
        "namespace_commit",
        "lts_series",
    }
    missing = sorted(required - config.keys())
    if missing:
        raise ApplyError(f"Missing {CONFIG_NAME} fields: {', '.join(missing)}")
    if config["distribution"] != "dj-orm":
        raise ApplyError(f"{CONFIG_NAME} must configure the dj-orm distribution.")
    if (
        not config["lts_series"]
        or not isinstance(config["lts_series"], list)
        or not all(isinstance(series, str) for series in config["lts_series"])
    ):
        raise ApplyError(f"{CONFIG_NAME} lts_series must be a non-empty array of strings.")
    return config


def normalize_upstream_version(django_ref: str) -> tuple[int, int, int]:
    match = FINAL_TAG_RE.fullmatch(django_ref)
    if match is None:
        raise ApplyError("Django ref must be a final numeric release tag such as 5.2.17 or 6.2.")
    raw_parts = [int(part) for part in match.group("parts").split(".")]
    if len(raw_parts) == 1:
        raw_parts.extend([0, 0])
    elif len(raw_parts) == 2:
        raw_parts.append(0)
    return raw_parts[0], raw_parts[1], raw_parts[2]


def release_series(django_ref: str) -> str:
    parts = django_ref.split(".")
    return ".".join(parts[:2]) if len(parts) > 1 else parts[0]


def assert_configured_lts(django_ref: str, config: dict[str, Any]) -> None:
    normalize_upstream_version(django_ref)
    series = release_series(django_ref)
    if series not in config["lts_series"]:
        configured = ", ".join(config["lts_series"])
        raise ApplyError(
            f"Django {django_ref} is not in the reviewed LTS series list ({configured})."
        )


def distribution_version(django_ref: str, revision: int) -> str:
    if revision < 0:
        raise ApplyError("The Djorm release revision must be zero or greater.")
    major, minor, patch = normalize_upstream_version(django_ref)
    return f"{major}.{minor}.{patch}.{revision}"


def assert_source_ready(source_repo: Path, config: dict[str, Any]) -> str:
    if git(source_repo, "status", "--porcelain"):
        raise ApplyError("The Djorm source checkout must be clean before applying an LTS tag.")
    expected_url = str(config["upstream_url"])
    remote = str(config["upstream_remote"])
    actual_url = git(source_repo, "remote", "get-url", remote, check=False)
    if actual_url != expected_url:
        raise ApplyError(
            f"Remote {remote!r} must point to {expected_url}; found {actual_url or 'nothing'}."
        )
    return git(source_repo, "rev-parse", "HEAD")


def fetch_exact_tag(source_repo: Path, remote: str, django_ref: str) -> str:
    remote_lines = git(
        source_repo,
        "ls-remote",
        "--tags",
        remote,
        f"refs/tags/{django_ref}",
        f"refs/tags/{django_ref}^{{}}",
    ).splitlines()
    if not remote_lines:
        raise ApplyError(f"Tag {django_ref!r} does not exist on the official Django remote.")
    run(
        ["git", "fetch", "--no-tags", remote, f"refs/tags/{django_ref}:refs/tags/{django_ref}"],
        cwd=source_repo,
        capture=False,
    )
    return git(source_repo, "rev-parse", f"refs/tags/{django_ref}^{{commit}}")


def commit_stack(source_repo: Path, base_commit: str, source_head: str) -> list[str]:
    if git(source_repo, "merge-base", base_commit, source_head) != base_commit:
        raise ApplyError("Configured upstream base is not an ancestor of the source branch.")
    output = git(
        source_repo, "rev-list", "--reverse", "--no-merges", f"{base_commit}..{source_head}"
    )
    commits = output.splitlines()
    if not commits:
        raise ApplyError("No Djorm commits exist after the configured upstream base.")
    return commits


def state_path(output: Path) -> Path:
    raw_path = git(output, "rev-parse", "--git-path", STATE_NAME)
    path = Path(raw_path)
    return path if path.is_absolute() else output / path


def save_state(output: Path, state: ApplyState) -> None:
    path = state_path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state), indent=2) + "\n", encoding="utf-8")


def load_state(output: Path) -> ApplyState:
    path = state_path(output)
    if not path.is_file():
        raise ApplyError(f"No interrupted Djorm application state exists for {output}.")
    return ApplyState(**json.loads(path.read_text(encoding="utf-8")))


def create_candidate(
    source_repo: Path,
    output: Path,
    django_ref: str,
    revision: int,
) -> ApplyState:
    if output.exists():
        raise ApplyError(f"Output path already exists: {output}")
    config = read_config(source_repo)
    source_head = assert_source_ready(source_repo, config)
    assert_configured_lts(django_ref, config)
    django_commit = fetch_exact_tag(source_repo, str(config["upstream_remote"]), django_ref)
    commits = commit_stack(source_repo, str(config["upstream_base_commit"]), source_head)
    namespace_commit = str(config["namespace_commit"])
    if namespace_commit not in commits:
        raise ApplyError("Configured namespace commit is not in the Djorm commit stack.")

    branch = f"release/django-{django_ref}"
    if git(source_repo, "show-ref", "--verify", f"refs/heads/{branch}", check=False):
        raise ApplyError(f"Local branch already exists: {branch}")
    output.parent.mkdir(parents=True, exist_ok=True)
    run(
        ["git", "worktree", "add", "-b", branch, str(output), django_commit],
        cwd=source_repo,
        capture=False,
    )
    state = ApplyState(
        source_repo=str(source_repo),
        source_head=source_head,
        output=str(output),
        branch=branch,
        django_ref=django_ref,
        django_commit=django_commit,
        revision=revision,
        commits=commits,
        namespace_commit=namespace_commit,
    )
    save_state(output, state)
    return state


def cherry_pick_in_progress(output: Path) -> bool:
    return bool(git(output, "rev-parse", "--verify", "CHERRY_PICK_HEAD", check=False))


def unmerged_paths(output: Path) -> list[str]:
    return git(output, "diff", "--name-only", "--diff-filter=U").splitlines()


def deleted_paths(source_repo: Path, commit: str) -> set[str]:
    output = git(
        source_repo,
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "--diff-filter=D",
        "-r",
        f"{commit}^",
        commit,
    )
    return set(output.splitlines())


def resolve_expected_deletions(output: Path, source_repo: Path, commit: str) -> list[str]:
    expected_deletions = deleted_paths(source_repo, commit)
    unresolved: list[str] = []
    for file_name in unmerged_paths(output):
        if file_name in expected_deletions:
            run(["git", "rm", "--", file_name], cwd=output, capture=True)
        else:
            unresolved.append(file_name)
    return unresolved


def run_namespace_step(output: Path, source_repo: Path) -> str:
    script = source_repo / "scripts" / "rename_namespace.py"
    run(
        [sys.executable, str(script), "--repo-root", str(output)],
        cwd=source_repo,
        capture=False,
    )
    run(["git", "add", "-A"], cwd=output, capture=True)
    run(
        ["git", "commit", "-m", "[namespace] Rename django -> djorm mechanically"],
        cwd=output,
        capture=False,
    )
    return git(output, "rev-parse", "HEAD")


def start_cherry_pick(output: Path, source_repo: Path, commit: str) -> list[str]:
    result = run(["git", "cherry-pick", commit], cwd=output, check=False, capture=True)
    if result.returncode == 0:
        return []
    if not cherry_pick_in_progress(output):
        detail = result.stderr.strip() or result.stdout.strip() or "unknown Git error"
        raise ApplyError(f"Could not cherry-pick {commit}: {detail}")
    unresolved = resolve_expected_deletions(output, source_repo, commit)
    if unresolved:
        return unresolved
    finish_cherry_pick(output)
    return []


def continue_current_cherry_pick(output: Path, source_repo: Path, commit: str) -> list[str]:
    if not cherry_pick_in_progress(output):
        return []
    unresolved = resolve_expected_deletions(output, source_repo, commit)
    if unresolved:
        return unresolved
    if unmerged_paths(output):
        return unmerged_paths(output)
    finish_cherry_pick(output)
    return []


def finish_cherry_pick(output: Path) -> None:
    staged = run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=output,
        check=False,
        capture=True,
    )
    if staged.returncode == 0:
        run(["git", "cherry-pick", "--skip"], cwd=output, capture=False)
    else:
        run(
            ["git", "-c", "core.editor=true", "cherry-pick", "--continue"],
            cwd=output,
            capture=False,
        )


def report_conflicts(output: Path, unresolved: list[str]) -> None:
    print("Upstream changed retained Djorm code. Resolve and stage these files:", file=sys.stderr)
    for file_name in unresolved:
        print(f"  {file_name}", file=sys.stderr)
    print(
        "Resume with: uv run python scripts/apply_django_lts.py "
        f"--continue --output {shlex.quote(str(output))}",
        file=sys.stderr,
    )


def update_version_file(output: Path, version: str) -> None:
    version_path = output / "djorm" / "_version.py"
    original = version_path.read_text(encoding="utf-8")
    rewritten, count = re.subn(
        r'^__version__\s*=\s*["\'][^"\']+["\']$',
        f'__version__ = "{version}"',
        original,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise ApplyError(f"Could not update distribution version in {version_path}.")
    version_path.write_text(rewritten, encoding="utf-8")


def write_generated_config(output: Path, state: ApplyState) -> None:
    series = release_series(state.django_ref)
    source_config = read_config(Path(state.source_repo))
    lts_series = ", ".join(f'"{series}"' for series in source_config["lts_series"])
    text = "\n".join(
        [
            "schema = 1",
            'distribution = "dj-orm"',
            f'yapc_commit = "{source_config["yapc_commit"]}"',
            'upstream_remote = "upstream"',
            'upstream_url = "https://github.com/django/django.git"',
            f'upstream_ref = "{state.django_ref}"',
            f'upstream_series = "{series}"',
            f"lts_series = [{lts_series}]",
            f'upstream_base_commit = "{state.django_commit}"',
            f'namespace_commit = "{state.generated_namespace_commit}"',
            f"release_revision = {state.revision}",
            "",
        ]
    )
    (output / CONFIG_NAME).write_text(text, encoding="utf-8")


def finalize(output: Path, state: ApplyState, *, verify: bool) -> None:
    version = distribution_version(state.django_ref, state.revision)
    update_version_file(output, version)
    write_generated_config(output, state)

    if verify:
        for command in (
            ["make", "check"],
            ["make", "test"],
            ["make", "build"],
            ["make", "check-dist"],
            ["make", "inspect-dist"],
        ):
            run(command, cwd=output, capture=False)

    allowed_changes = {CONFIG_NAME, "djorm/_version.py"}
    changed_paths = set(git(output, "diff", "--name-only").splitlines())
    changed_paths.update(git(output, "diff", "--cached", "--name-only").splitlines())
    changed_paths.update(git(output, "ls-files", "--others", "--exclude-standard").splitlines())
    unexpected = sorted(changed_paths - allowed_changes)
    if unexpected:
        raise ApplyError("Verification changed unexpected files: " + ", ".join(unexpected))

    run(["git", "add", CONFIG_NAME, "djorm/_version.py"], cwd=output, capture=True)
    staged_diff = run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=output,
        check=False,
        capture=True,
    )
    if staged_diff.returncode == 0:
        raise ApplyError("Generated provenance and version did not change.")
    run(
        ["git", "commit", "-m", f"[lts] Base Djorm on Django {state.django_ref}"],
        cwd=output,
        capture=False,
    )
    state_path(output).unlink(missing_ok=True)
    print(f"Created {state.branch} at {output}")
    print(f"Distribution version: {version}")


def validate_resume_state(state: ApplyState, output: Path) -> None:
    source_repo = Path(state.source_repo)
    if not source_repo.is_dir():
        raise ApplyError(f"Recorded source checkout no longer exists: {source_repo}")
    if Path(state.output).resolve() != output:
        raise ApplyError(f"State belongs to a different output path: {state.output}")
    if git(source_repo, "rev-parse", "HEAD") != state.source_head:
        raise ApplyError("The source branch changed after this application started.")
    if git(source_repo, "status", "--porcelain"):
        raise ApplyError("The source checkout became dirty after this application started.")
    branch = git(output, "branch", "--show-current")
    if branch != state.branch:
        raise ApplyError(
            f"Output must remain on {state.branch}; found {branch or 'detached HEAD'}."
        )


def apply_remaining(state: ApplyState, *, verify: bool) -> int:
    output = Path(state.output)
    source_repo = Path(state.source_repo)

    if state.next_index < len(state.commits) and cherry_pick_in_progress(output):
        current_commit = state.commits[state.next_index]
        unresolved = continue_current_cherry_pick(output, source_repo, current_commit)
        if unresolved:
            save_state(output, state)
            report_conflicts(output, unresolved)
            return 2
        state.next_index += 1
        save_state(output, state)

    while state.next_index < len(state.commits):
        commit = state.commits[state.next_index]
        if commit == state.namespace_commit:
            state.generated_namespace_commit = run_namespace_step(output, source_repo)
            state.next_index += 1
            save_state(output, state)
            continue

        unresolved = start_cherry_pick(output, source_repo, commit)
        if unresolved:
            save_state(output, state)
            report_conflicts(output, unresolved)
            return 2
        state.next_index += 1
        save_state(output, state)

    finalize(output, state, verify=verify)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--django-ref", help="Exact final Django LTS tag, for example 5.2.17")
    parser.add_argument("--output", required=True, type=Path, help="New candidate worktree path")
    parser.add_argument("--revision", type=int, default=0, help="Djorm-only rebuild revision")
    parser.add_argument("--continue", dest="resume", action="store_true")
    parser.add_argument("--no-verify", action="store_true", help="Skip the final package gate")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output.resolve()
    try:
        if args.resume:
            if args.django_ref is not None:
                raise ApplyError("--django-ref cannot be combined with --continue.")
            state = load_state(output)
            validate_resume_state(state, output)
        else:
            if args.django_ref is None:
                raise ApplyError("--django-ref is required unless --continue is used.")
            source_repo = repo_root()
            state = create_candidate(source_repo, output, args.django_ref, args.revision)
        return apply_remaining(state, verify=not args.no_verify)
    except (ApplyError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
