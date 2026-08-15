from pathlib import Path

import pytest

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib

from scripts.apply_django_lts import (
    ApplyError,
    assert_configured_lts,
    distribution_version,
    normalize_upstream_version,
    release_series,
)
from scripts.rename_namespace import rewrite_python


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
    assert_configured_lts(django_ref, {"lts_series": ["5.2", "6.2"]})


@pytest.mark.parametrize("django_ref", ["5.1", "6.0.8", "2028.3"])
def test_reject_unreviewed_series(django_ref: str) -> None:
    with pytest.raises(ApplyError):
        assert_configured_lts(django_ref, {"lts_series": ["5.2", "6.2"]})


def test_distribution_version_records_rebuild_revision() -> None:
    assert distribution_version("5.2.17", 3) == "5.2.17.3"


def test_reject_negative_revision() -> None:
    with pytest.raises(ApplyError):
        distribution_version("5.2.17", -1)


def test_maintenance_config_records_distribution_and_template() -> None:
    root = Path(__file__).resolve().parents[2]
    with (root / ".djorm-maintenance.toml").open("rb") as config_file:
        config = tomllib.load(config_file)
    assert config["distribution"] == "dj-orm"
    assert len(config["yapc_commit"]) == 40
    assert config["lts_series"] == ["5.2", "6.2"]


def test_namespace_rewrite_preserves_pre_312_fstring_syntax(tmp_path: Path) -> None:
    source = tmp_path / "example.py"
    source.write_text(
        "from " + "django" + ".db import models\nmessage = f'Value: {models!r}'\n",
        encoding="utf-8",
    )

    assert rewrite_python(source)
    rewritten = source.read_text(encoding="utf-8")
    assert "djorm" in rewritten
    assert "{models!r}" in rewritten
    assert rewritten == "from djorm.db import models\nmessage = f'Value: {models!r}'\n"
