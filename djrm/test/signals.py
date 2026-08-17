import os
import time

from asgiref.local import Local

from djrm.core.signals import setting_changed
from djrm.db import connections, router
from djrm.db.utils import ConnectionRouter
from djrm.dispatch import Signal, receiver
from djrm.utils import timezone
from djrm.utils.formats import FORMAT_SETTINGS, reset_format_cache
from djrm.utils.functional import empty

template_rendered = Signal()


@receiver(setting_changed)
def update_installed_apps(*, setting, **kwargs):
    if setting == "INSTALLED_APPS":
        from djrm.core.management import get_commands
        from djrm.utils.translation import trans_real

        get_commands.cache_clear()
        trans_real._translations = {}


@receiver(setting_changed)
def update_connections_time_zone(*, setting, **kwargs):
    if setting == "TIME_ZONE":
        if hasattr(time, "tzset"):
            if kwargs["value"]:
                os.environ["TZ"] = kwargs["value"]
            else:
                os.environ.pop("TZ", None)
            time.tzset()
        timezone.get_default_timezone.cache_clear()

    if setting in {"TIME_ZONE", "USE_TZ"}:
        for conn in connections.all(initialized_only=True):
            try:
                del conn.timezone
            except AttributeError:
                pass
            try:
                del conn.timezone_name
            except AttributeError:
                pass
            conn.ensure_timezone()


@receiver(setting_changed)
def storages_changed(*, setting, **kwargs):
    if setting == "STORAGES":
        from djrm.core.files.storage import default_storage, storages

        try:
            del storages.backends
        except AttributeError:
            pass
        storages._backends = None
        storages._storages = {}
        default_storage._wrapped = empty


@receiver(setting_changed)
def clear_routers_cache(*, setting, **kwargs):
    if setting == "DATABASE_ROUTERS":
        router.routers = ConnectionRouter().routers


@receiver(setting_changed)
def clear_serializers_cache(*, setting, **kwargs):
    if setting == "SERIALIZATION_MODULES":
        from djrm.core import serializers

        serializers._serializers = {}


@receiver(setting_changed)
def language_changed(*, setting, **kwargs):
    if setting in {"LANGUAGES", "LANGUAGE_CODE", "LOCALE_PATHS"}:
        from djrm.utils.translation import trans_real

        trans_real._default = None
        trans_real._active = Local()
    if setting in {"LANGUAGES", "LOCALE_PATHS"}:
        from djrm.utils.translation import trans_real

        trans_real._translations = {}
        trans_real.translation_catalog_exists.cache_clear()


@receiver(setting_changed)
def localize_settings_changed(*, setting, **kwargs):
    if setting in FORMAT_SETTINGS or setting == "USE_THOUSAND_SEPARATOR":
        reset_format_cache()
