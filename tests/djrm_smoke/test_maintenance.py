from pathlib import Path
import subprocess

import pytest

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib

from djrm._version import __version__ as package_version
from scripts.apply_django_lts import (
    ApplyError,
    ApplyState,
    apply_delta,
    assert_configured_lts,
    distribution_version,
    fully_deleted_directory_prefixes,
    is_fork_owned,
    is_pruned_path,
    lts_version_majors,
    normalize_upstream_version,
    parse_distribution_version,
    release_series,
)
from scripts.audit_upstream_delta import (
    baseline_text,
    syntax_dump,
    validate_report,
)
from scripts.rename_namespace import rewrite_python

LTS_VERSION_MAJORS = {"5.2": 0, "6.2": 1}


def run_git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@pytest.mark.parametrize(
    ("django_ref", "expected"),
    [
        ("5.2", (5, 2, 0)),
        ("5.2.17", (5, 2, 17)),
        ("6.2", (6, 2, 0)),
        ("2028", (2028, 0, 0)),
        ("2028.3", (2028, 3, 0)),
    ],
)
def test_normalize_upstream_version(django_ref: str, expected: tuple[int, int, int]) -> None:
    assert normalize_upstream_version(django_ref) == expected


@pytest.mark.parametrize("django_ref", ["5.2rc1", "stable/5.2.x"])
def test_reject_non_final_refs(django_ref: str) -> None:
    with pytest.raises(ApplyError):
        normalize_upstream_version(django_ref)


@pytest.mark.parametrize(("django_ref", "expected"), [("5.2.17", "5.2"), ("2028", "2028")])
def test_release_series(django_ref: str, expected: str) -> None:
    assert release_series(django_ref) == expected


@pytest.mark.parametrize("django_ref", ["5.2.17", "6.2"])
def test_accept_reviewed_lts_series(django_ref: str) -> None:
    assert_configured_lts(django_ref, {"lts_version_majors": LTS_VERSION_MAJORS})


@pytest.mark.parametrize("django_ref", ["5.1", "6.0.8", "2028.3"])
def test_reject_unreviewed_series(django_ref: str) -> None:
    with pytest.raises(ApplyError):
        assert_configured_lts(django_ref, {"lts_version_majors": LTS_VERSION_MAJORS})


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("0.1.0", (0, 1, 0)),
        ("1.0.0", (1, 0, 0)),
        ("12.34.56", (12, 34, 56)),
    ],
)
def test_parse_distribution_version(version: str, expected: tuple[int, int, int]) -> None:
    assert parse_distribution_version(version) == expected


@pytest.mark.parametrize("version", ["5.2.17.0", "0.01.0", "v0.1.0", "0.1"])
def test_reject_non_semver_distribution_versions(version: str) -> None:
    with pytest.raises(ApplyError):
        parse_distribution_version(version)


def test_distribution_version_increments_patch_for_same_django_tag() -> None:
    assert (
        distribution_version(
            "5.2.17",
            1,
            current_django_ref="5.2.17",
            current_version="0.1.0",
            version_majors=LTS_VERSION_MAJORS,
        )
        == "0.1.1"
    )


def test_distribution_version_increments_minor_for_new_django_patch() -> None:
    assert (
        distribution_version(
            "5.2.18",
            0,
            current_django_ref="5.2.17",
            current_version="0.1.2",
            version_majors=LTS_VERSION_MAJORS,
        )
        == "0.2.0"
    )


def test_distribution_version_increments_major_for_new_lts() -> None:
    assert (
        distribution_version(
            "6.2",
            0,
            current_django_ref="5.2.17",
            current_version="0.1.2",
            version_majors=LTS_VERSION_MAJORS,
        )
        == "1.0.0"
    )


def test_reject_negative_patch() -> None:
    with pytest.raises(ApplyError):
        distribution_version(
            "5.2.17",
            -1,
            current_django_ref="5.2.17",
            current_version="0.1.0",
            version_majors=LTS_VERSION_MAJORS,
        )


def test_reject_nonincrementing_rebuild_patch() -> None:
    with pytest.raises(ApplyError, match="greater than 2"):
        distribution_version(
            "5.2.17",
            2,
            current_django_ref="5.2.17",
            current_version="0.1.2",
            version_majors=LTS_VERSION_MAJORS,
        )


def test_reject_patch_for_first_release_from_new_django_tag() -> None:
    with pytest.raises(ApplyError, match="must use --patch 0"):
        distribution_version(
            "5.2.18",
            1,
            current_django_ref="5.2.17",
            current_version="0.1.2",
            version_majors=LTS_VERSION_MAJORS,
        )


@pytest.mark.parametrize(
    "mapping",
    [
        {},
        {"5.2": 1},
        {"5.2": 0, "6.2": 2},
        {"5.2": True},
    ],
)
def test_reject_invalid_lts_version_major_mappings(mapping: dict[str, int]) -> None:
    with pytest.raises(ApplyError):
        lts_version_majors({"lts_version_majors": mapping})


@pytest.mark.parametrize(
    "path",
    [
        ".github/workflows/main.yml",
        ".pre-commit-config.yaml",
        ".djrm-upstream-delta.toml",
        "djrm/_ext/forms.py",
        "pyproject.toml",
        "scripts/apply_django_lts.py",
        "scripts/audit_upstream_delta.py",
        "tests/djrm_smoke/test_distribution.py",
        "tox.ini",
    ],
)
def test_lts_application_prefers_reviewed_infrastructure(path: str) -> None:
    assert is_fork_owned(path)


def test_lts_application_reviews_retained_runtime_conflicts() -> None:
    assert not is_fork_owned("djrm/db/models/query.py")


def test_lts_application_keeps_fully_deleted_directories_pruned() -> None:
    baseline_paths = {
        "djrm/contrib/gis/__init__.py",
        "djrm/contrib/gis/db/models/fields.py",
        "djrm/contrib/postgres/__init__.py",
        "djrm/db/models/query.py",
        "tests/gis_tests/geos_tests/test_geos.py",
        "tests/gis_tests/test_runner.py",
        "tests/model_tests/test_models.py",
    }
    source_paths = {
        "djrm/contrib/postgres/__init__.py",
        "djrm/db/models/query.py",
        "tests/model_tests/test_models.py",
    }

    assert fully_deleted_directory_prefixes(baseline_paths, source_paths) == (
        "tests/gis_tests/",
        "djrm/contrib/gis/",
    )


def test_lts_application_collapses_nested_deleted_directories() -> None:
    baseline_paths = {
        "docs/_ext/links.py",
        "docs/ref/models.txt",
        "tests/model_tests/test_models.py",
    }
    source_paths = {"tests/model_tests/test_models.py"}

    assert fully_deleted_directory_prefixes(baseline_paths, source_paths) == ("docs/",)


def test_lts_application_does_not_prune_retained_parent_directory() -> None:
    baseline_paths = {
        "tests/gis_tests/test_runner.py",
        "tests/model_tests/test_models.py",
    }
    source_paths = {"tests/model_tests/test_models.py"}

    deleted = fully_deleted_directory_prefixes(baseline_paths, source_paths)

    assert "tests/" not in deleted


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("djrm/conf/locale/fr/LC_MESSAGES/django.po", True),
        ("djrm/conf/locale/fr/LC_MESSAGES/django.mo", False),
        ("djrm/db/models/query.py", False),
    ],
)
def test_lts_application_prunes_translation_sources_only(
    path: str,
    expected: bool,
) -> None:
    assert is_pruned_path(path) is expected


def test_lts_application_removes_new_upstream_files_from_pruned_directory(
    tmp_path: Path,
) -> None:
    source_repo = tmp_path / "source"
    source_repo.mkdir()
    run_git(source_repo, "init", "-b", "main")
    run_git(source_repo, "config", "user.name", "djrm tests")
    run_git(source_repo, "config", "user.email", "tests@example.invalid")

    (source_repo / "kept").mkdir()
    (source_repo / "kept" / "model.py").write_text("baseline\n", encoding="utf-8")
    (source_repo / "locale" / "en" / "LC_MESSAGES").mkdir(parents=True)
    (source_repo / "locale" / "en" / "LC_MESSAGES" / "django.mo").write_bytes(b"compiled")
    (source_repo / "pruned").mkdir()
    (source_repo / "pruned" / "old.py").write_text("old\n", encoding="utf-8")
    run_git(
        source_repo,
        "add",
        "kept/model.py",
        "locale/en/LC_MESSAGES/django.mo",
        "pruned/old.py",
    )
    run_git(source_repo, "commit", "-m", "baseline")
    baseline_tree = run_git(source_repo, "rev-parse", "HEAD^{tree}")

    run_git(source_repo, "switch", "-c", "maintained")
    run_git(source_repo, "rm", "pruned/old.py")
    run_git(source_repo, "commit", "-m", "prune unused directory")
    source_head = run_git(source_repo, "rev-parse", "HEAD")

    run_git(source_repo, "switch", "main")
    (source_repo / "locale" / "en" / "LC_MESSAGES" / "django.po").write_text(
        "new translation source\n",
        encoding="utf-8",
    )
    (source_repo / "pruned" / "new.py").write_text("new upstream file\n", encoding="utf-8")
    run_git(source_repo, "add", "locale/en/LC_MESSAGES/django.po", "pruned/new.py")
    run_git(source_repo, "commit", "-m", "add upstream file")
    target_head = run_git(source_repo, "rev-parse", "HEAD")

    output = tmp_path / "candidate"
    run_git(source_repo, "worktree", "add", "--detach", str(output), target_head)
    state = ApplyState(
        source_repo=str(source_repo),
        source_head=source_head,
        output=str(output),
        branch="test",
        django_ref="5.2.18",
        django_commit=target_head,
        release_version="0.2.0",
        baseline_tree=baseline_tree,
    )

    assert apply_delta(source_repo, output, state) == []
    assert run_git(output, "ls-files", "pruned") == ""
    assert not (output / "pruned").exists()
    assert run_git(output, "ls-files", "locale/en/LC_MESSAGES/django.po") == ""
    assert run_git(output, "ls-files", "locale/en/LC_MESSAGES/django.mo")


def test_maintenance_config_records_distribution_and_template() -> None:
    root = Path(__file__).resolve().parents[2]
    with (root / ".djrm-maintenance.toml").open("rb") as config_file:
        config = tomllib.load(config_file)
    assert config["schema"] == 3
    assert config["distribution"] == "djrm"
    assert config["application"] == "tree-delta"
    assert len(config["yapc_commit"]) == 40
    assert config["lts_version_majors"] == LTS_VERSION_MAJORS
    assert config["release_version"] == package_version
    assert "namespace_commit" not in config


def test_delta_audit_ignores_docstrings_only_for_executable_ast() -> None:
    first = b'def example():\n    """first"""\n    return 1\n'
    second = b'def example():\n    """second"""\n    return 1\n'

    assert syntax_dump(first, executable=False) != syntax_dump(
        second,
        executable=False,
    )
    assert syntax_dump(first, executable=True) == syntax_dump(
        second,
        executable=True,
    )


def test_delta_baseline_round_trip_and_drift_detection() -> None:
    report = {
        "upstream_ref": "5.2.17",
        "upstream_commit": "a" * 40,
        "djrm": {
            "common": 2,
            "byte_differences": 1,
            "raw_ast_differences": ["djrm/db.py"],
            "executable_ast_differences": ["djrm/db.py"],
            "non_ast_byte_differences": 0,
            "upstream_only": 1,
            "upstream_only_sha256": "b" * 64,
            "fork_only": 1,
            "fork_only_sha256": "c" * 64,
        },
        "tests": {
            "common": 2,
            "byte_differences": 0,
            "raw_ast_differences": [],
            "executable_ast_differences": [],
            "non_ast_byte_differences": 0,
            "upstream_only": 0,
            "upstream_only_sha256": "d" * 64,
            "fork_only": 0,
            "fork_only_sha256": "d" * 64,
        },
    }
    baseline = tomllib.loads(baseline_text(report))

    assert validate_report(report, baseline) == []

    report["djrm"]["executable_ast_differences"] = ["djrm/new_drift.py"]
    assert validate_report(report, baseline) == ["djrm executable AST allowlist changed"]


def test_namespace_rewrite_preserves_pre_312_fstring_syntax(tmp_path: Path) -> None:
    source = tmp_path / "example.py"
    source.write_text(
        "from " + "django" + ".db import models\nmessage = f'Value: {models!r}'\n",
        encoding="utf-8",
    )

    assert rewrite_python(source)
    rewritten = source.read_text(encoding="utf-8")
    assert "djrm" in rewritten
    assert "{models!r}" in rewritten
    assert rewritten == "from djrm.db import models\nmessage = f'Value: {models!r}'\n"
