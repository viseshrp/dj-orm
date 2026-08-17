import subprocess
import sys


def run_script(source: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", source],
        text=True,
        capture_output=True,
    )


def test_storage_override_rebuilds_default_storage() -> None:
    result = run_script(
        """
from djrm.conf import settings
settings.configure(
    DATABASES={"default": {"ENGINE": "djrm.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[],
)
import djrm
djrm.setup()
from djrm.conf import DEFAULT_STORAGE_ALIAS
from djrm.core.files.storage import FileSystemStorage, InMemoryStorage, default_storage
from djrm.test import override_settings
assert isinstance(default_storage, FileSystemStorage)
with override_settings(
    STORAGES={DEFAULT_STORAGE_ALIAS: {"BACKEND": "djrm.core.files.storage.InMemoryStorage"}}
):
    assert isinstance(default_storage, InMemoryStorage)
"""
    )

    assert result.returncode == 0, result.stderr


def test_installed_apps_override_clears_command_discovery_cache() -> None:
    result = run_script(
        """
from djrm.conf import settings
settings.configure(
    DATABASES={"default": {"ENGINE": "djrm.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[],
)
import djrm
djrm.setup()
from djrm.core.management import get_commands
from djrm.test import override_settings
get_commands()
assert get_commands.cache_info().currsize == 1
with override_settings(INSTALLED_APPS=["djrm.contrib.contenttypes"]):
    assert get_commands.cache_info().currsize == 0
"""
    )

    assert result.returncode == 0, result.stderr
