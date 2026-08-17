import ast
from importlib.metadata import version
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

from djrm._version import __version__
from djrm.utils.translation import templatize


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


def test_removed_url_prefix_helpers_are_safe() -> None:
    from djrm._ext.setup_helpers import (
        add_script_prefix_if_available,
        set_script_prefix_if_available,
    )

    assert add_script_prefix_if_available("relative") == "relative"
    assert add_script_prefix_if_available("/absolute") == "/absolute"
    set_script_prefix_if_available(None)


def test_removed_forms_fail_only_when_formfield_is_requested() -> None:
    from djrm.db import models

    with pytest.raises(ImportError, match="djrm.forms is not available"):
        models.JSONField().formfield()


def test_missing_module_guard_rejects_internal_import_failures() -> None:
    from djrm._ext.imports import is_expected_missing_module

    expected = ModuleNotFoundError(name="djrm.forms")
    internal = ModuleNotFoundError(name="retained_dependency")

    assert is_expected_missing_module(expected, "djrm.forms")
    assert not is_expected_missing_module(internal, "djrm.forms")


def test_retained_check_imports_propagate_internal_failures() -> None:
    script = """
import importlib

original = importlib.import_module
def import_with_failure(name, *args, **kwargs):
    if name == "djrm.core.checks.database":
        raise ModuleNotFoundError(name="retained_dependency")
    return original(name, *args, **kwargs)

importlib.import_module = import_with_failure
try:
    import djrm.core.checks
except ModuleNotFoundError as error:
    assert error.name == "retained_dependency"
else:
    raise AssertionError("internal check import failure was suppressed")
"""
    result = subprocess.run([sys.executable, "-c", script], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_logging_fallback_is_limited_to_removed_default_reporter() -> None:
    default_script = """
from djrm.conf import settings
settings.configure()
from djrm.utils.log import AdminEmailHandler, ExceptionReporterFallback
assert AdminEmailHandler().reporter_class is ExceptionReporterFallback
"""
    custom_script = """
from djrm.conf import settings
settings.configure(DEFAULT_EXCEPTION_REPORTER="custom_reporter.Reporter")
from djrm.utils.log import AdminEmailHandler
try:
    AdminEmailHandler()
except ModuleNotFoundError as error:
    assert error.name == "custom_reporter"
else:
    raise AssertionError("missing custom reporter was suppressed")
"""

    for script in (default_script, custom_script):
        result = subprocess.run([sys.executable, "-c", script], text=True, capture_output=True)
        assert result.returncode == 0, result.stderr


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


def test_source_has_no_gis_package() -> None:
    root = Path(__file__).resolve().parents[2]
    assert not (root / "djrm" / "contrib" / "gis").exists()


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


def test_templatize_without_template_engine() -> None:
    output = templatize(
        "{% translate 'Greeting' context 'button' %}\n"
        "{% blocktranslate trimmed count total=items %}"
        "One {{ item }}{% plural %}Many {{ item }}s"
        "{% endblocktranslate %}"
    )

    assert "pgettext(u'button', u'Greeting')" in output
    assert "ngettext(u'One %(item)s', u'Many %(item)ss', count)" in output


def test_templatize_respects_verbatim_blocks() -> None:
    output = templatize(
        "{% verbatim %}{% translate 'Not extracted' %}{% endverbatim %}{% translate 'Extracted' %}"
    )

    assert "Not extracted" not in output
    assert "gettext(u'Extracted')" in output


def test_templatize_reports_nested_translation_block() -> None:
    source = "{% blocktranslate %}bad {% if value %}nest{% endblocktranslate %}"

    with pytest.raises(SyntaxError, match=r"if value .*file example\.html, line 1"):
        templatize(source, origin="example.html")


def test_removed_html_assertion_fails_explicitly() -> None:
    from djrm.test import SimpleTestCase

    with pytest.raises(AssertionError, match="HTML parsing is not available"):
        SimpleTestCase().assertHTMLEqual("<p>one</p>", "<p>one</p>")


def test_live_server_case_is_not_exported() -> None:
    import djrm.test

    assert not hasattr(djrm.test, "LiveServerTestCase")


def test_source_compiles_on_supported_python(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    environment = dict(os.environ)
    environment["PYTHONPYCACHEPREFIX"] = str(tmp_path / "pycache")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            "-f",
            "-x",
            r"tests/test_runner_apps/tagged/tests_syntax_error\.py$",
            "djrm",
            "tests",
        ],
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
