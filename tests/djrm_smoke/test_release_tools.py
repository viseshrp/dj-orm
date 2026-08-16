from io import BytesIO
from pathlib import Path
import subprocess
import tarfile
import zipfile

import pytest

from scripts.check_coverage import read_targets
from scripts.check_release import validate
from scripts.inspect_dist import (
    InspectionError,
    inspect_sdist,
    inspect_wheel,
)


def run_git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def test_release_validation_accepts_matching_clean_repository(tmp_path: Path) -> None:
    (tmp_path / "djrm").mkdir()
    (tmp_path / "djrm" / "_version.py").write_text(
        '__version__ = "0.1.1"\n',
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "djrm"\n',
        encoding="utf-8",
    )
    (tmp_path / ".djrm-maintenance.toml").write_text(
        "\n".join(
            [
                "schema = 3",
                'distribution = "djrm"',
                'upstream_ref = "5.2.17"',
                'upstream_series = "5.2"',
                'release_version = "0.1.1"',
                'lts_version_majors = { "5.2" = 0, "6.2" = 1 }',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "CHANGELOG.md").write_text(
        "## [0.1.1] - 2026-08-16\n",
        encoding="utf-8",
    )
    run_git(tmp_path, "init", "-b", "main")
    run_git(tmp_path, "config", "user.name", "djrm tests")
    run_git(tmp_path, "config", "user.email", "tests@example.invalid")
    run_git(tmp_path, "add", ".")
    run_git(tmp_path, "commit", "-m", "release")

    assert validate(tmp_path, "v0.1.1") == []
    assert "tag 'v9.0.0' does not match package version '0.1.1'" in validate(
        tmp_path,
        "v9.0.0",
    )


def write_wheel(path: Path, extra: tuple[str, ...] = ()) -> None:
    names = (
        "djrm/__init__.py",
        "djrm/_version.py",
        "djrm/db/models/__init__.py",
        "djrm/core/management/__init__.py",
        "djrm/conf/locale/fr/LC_MESSAGES/django.mo",
        "djrm-0.1.1.dist-info/METADATA",
        *extra,
    )
    with zipfile.ZipFile(path, "w") as archive:
        for name in names:
            archive.writestr(name, b"content")


def test_wheel_inspector_accepts_required_package(tmp_path: Path) -> None:
    wheel = tmp_path / "djrm.whl"
    write_wheel(wheel)

    inspect_wheel(wheel)


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        (("django/__init__.py",), "forbidden django package"),
        (("djrm/contrib/gis/__init__.py",), "excluded GIS package"),
        (("djrm/conf/locale/fr/LC_MESSAGES/django.po",), "gettext source"),
    ],
)
def test_wheel_inspector_rejects_excluded_content(
    tmp_path: Path,
    extra: tuple[str, ...],
    message: str,
) -> None:
    wheel = tmp_path / "djrm.whl"
    write_wheel(wheel, extra)

    with pytest.raises(InspectionError, match=message):
        inspect_wheel(wheel)


def write_sdist(path: Path, *, include_runner: bool = True) -> None:
    suffixes = {
        ".djrm-upstream-delta.toml",
        ".github/pull_request_template.md",
        "LIBRARY_AUDIT.md",
        "README.md",
        "MAINTENANCE.md",
        "djrm/conf/locale/fr/LC_MESSAGES/django.mo",
        "scripts/apply_django_lts.py",
        "scripts/audit_upstream_delta.py",
        "scripts/check_coverage.py",
        "scripts/check_path_case.py",
        "scripts/test_external_databases.py",
        "tests/test_sqlite.py",
        "tests/basic/tests.py",
        "tests/djrm_smoke/test_distribution.py",
        "tests/e2e/compose.yaml",
    }
    if include_runner:
        suffixes.add("tests/runtests.py")
    with tarfile.open(path, "w:gz") as archive:
        for suffix in suffixes:
            info = tarfile.TarInfo(f"djrm-0.1.1/{suffix}")
            content = b"content"
            info.size = len(content)
            archive.addfile(info, BytesIO(content))


def test_sdist_inspector_accepts_reproducible_source(tmp_path: Path) -> None:
    sdist = tmp_path / "djrm.tar.gz"
    write_sdist(sdist)

    inspect_sdist(sdist)


def test_sdist_inspector_requires_retained_test_runner(tmp_path: Path) -> None:
    sdist = tmp_path / "djrm.tar.gz"
    write_sdist(sdist, include_runner=False)

    with pytest.raises(InspectionError, match="tests/runtests.py"):
        inspect_sdist(sdist)


def test_coverage_baselines_cover_modified_and_fork_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    targets = read_targets(root)

    assert targets["modified_floor"] >= 65
    assert targets["fork_floor"] >= 44
    assert "djrm/utils/translation/template.py" in targets["modified_paths"]
    assert "scripts/check_release.py" in targets["fork_paths"]
