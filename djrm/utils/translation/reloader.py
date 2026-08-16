from pathlib import Path

from asgiref.local import Local

from djrm._ext.imports import is_expected_missing_module
from djrm.apps import apps

try:
    from djrm.utils.autoreload import is_django_module
except ModuleNotFoundError as error:
    if not is_expected_missing_module(error, "djrm.utils.autoreload"):
        raise

    def is_django_module(module):
        return module.__name__.startswith("djrm.")


def watch_for_translation_changes(sender, **kwargs):
    """Register file watchers for .mo files in potential locale paths."""
    from djrm.conf import settings

    if settings.USE_I18N:
        directories = [Path("locale")]
        directories.extend(
            Path(config.path) / "locale"
            for config in apps.get_app_configs()
            if not is_django_module(config.module)
        )
        directories.extend(Path(p) for p in settings.LOCALE_PATHS)
        for path in directories:
            sender.watch_dir(path, "**/*.mo")


def translation_file_changed(sender, file_path, **kwargs):
    """Clear the internal translations cache if a .mo file is modified."""
    if file_path.suffix == ".mo":
        import gettext

        from djrm.utils.translation import trans_real

        gettext._translations = {}
        trans_real._translations = {}
        trans_real._default = None
        trans_real._active = Local()
        return True
