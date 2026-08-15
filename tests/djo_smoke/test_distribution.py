from importlib.metadata import version
from pathlib import Path
import subprocess
import sys

import pytest

from djo._version import __version__


def test_distribution_metadata_matches_version_module() -> None:
    assert version("dj-orm") == __version__


def test_standalone_sqlite_setup() -> None:
    script = """
import djo
from djo.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "djo.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[],
)
djo.setup()
from djo.db import models
assert models.Model is not None
"""
    result = subprocess.run([sys.executable, "-c", script], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_removed_forms_fail_only_when_formfield_is_requested() -> None:
    from djo.db import models

    with pytest.raises(ImportError, match="djo.forms is not available"):
        models.JSONField().formfield()


def test_module_cli_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "djo", "--help"],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "Available subcommands" in result.stdout


def test_source_has_no_django_package() -> None:
    root = Path(__file__).resolve().parents[2]
    assert not (root / "django").exists()
