import ast
from importlib.metadata import version
import os
from pathlib import Path
import re
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


def test_source_compiles_on_supported_python(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    environment = dict(os.environ)
    environment["PYTHONPYCACHEPREFIX"] = str(tmp_path / "pycache")
    result = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", "-f", "djo", "tests"],
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

    for feature_path in (root / "djo" / "db" / "backends").rglob("features.py"):
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
