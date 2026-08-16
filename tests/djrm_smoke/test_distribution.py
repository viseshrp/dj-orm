import ast
from importlib.metadata import version
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

from djrm._version import __version__


def test_distribution_metadata_matches_version_module() -> None:
    assert version("djrm") == __version__


def test_standalone_sqlite_setup() -> None:
    script = """
import djrm
from djrm.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "djrm.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[],
)
djrm.setup()
from djrm.db import models
assert models.Model is not None
"""
    result = subprocess.run([sys.executable, "-c", script], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_removed_forms_fail_only_when_formfield_is_requested() -> None:
    from djrm.db import models

    with pytest.raises(ImportError, match="djrm.forms is not available"):
        models.JSONField().formfield()


def test_postgres_orm_imports_do_not_require_removed_forms() -> None:
    from djrm.contrib.postgres.aggregates import ArrayAgg
    from djrm.contrib.postgres.fields import (
        ArrayField,
        HStoreField,
        IntegerRangeField,
    )
    from djrm.db import models

    assert ArrayAgg("value") is not None
    fields = [
        ArrayField(models.IntegerField()),
        HStoreField(),
        IntegerRangeField(),
    ]
    for field in fields:
        with pytest.raises(ImportError, match="djrm.forms is not available"):
            field.formfield()


def test_module_cli_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "djrm", "--help"],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "Available subcommands" in result.stdout


def test_source_has_no_django_package() -> None:
    root = Path(__file__).resolve().parents[2]
    assert not (root / "django").exists()


def test_source_contains_compiled_translation_catalogs_only() -> None:
    root = Path(__file__).resolve().parents[2]
    locale_root = root / "djrm" / "conf" / "locale"

    assert any(locale_root.rglob("django.mo"))
    assert not any(locale_root.rglob("*.po"))


def test_compiled_translation_catalogs_load() -> None:
    script = """
from djrm.conf import settings

settings.configure(USE_I18N=True, LANGUAGE_CODE="fr", INSTALLED_APPS=[])
import djrm
djrm.setup()
from djrm.utils.translation import activate, gettext
activate("fr")
assert gettext("January") == "janvier"
"""
    result = subprocess.run([sys.executable, "-c", script], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_source_compiles_on_supported_python(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    environment = dict(os.environ)
    environment["PYTHONPYCACHEPREFIX"] = str(tmp_path / "pycache")
    result = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", "-f", "djrm", "tests"],
        cwd=root,
        env=environment,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_backend_skip_references_use_retained_test_modules() -> None:
    root = Path(__file__).resolve().parents[2]
    tests_root = root / "tests"
    reference_pattern = re.compile(r"[a-z][\w]*(?:\.[\w]+){2,}")
    missing: list[str] = []

    for feature_path in (root / "djrm" / "db" / "backends").rglob("features.py"):
        tree = ast.parse(feature_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            reference = node.value
            if reference_pattern.fullmatch(reference) is None:
                continue
            parts = reference.split(".")
            if not (tests_root / parts[0]).is_dir():
                continue
            module_exists = any(
                tests_root.joinpath(*parts[:length]).with_suffix(".py").is_file()
                for length in range(1, len(parts) + 1)
            )
            if not module_exists:
                missing.append(f"{feature_path.relative_to(root)}: {reference}")

    assert not missing, "\n".join(sorted(missing))
