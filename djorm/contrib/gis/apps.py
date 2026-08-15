from djorm.apps import AppConfig
from djorm.core import serializers
from djorm.utils.translation import gettext_lazy as _


class GISConfig(AppConfig):
    default_auto_field = 'djorm.db.models.AutoField'
    name = 'djorm.contrib.gis'
    verbose_name = _("GIS")

    def ready(self):
        serializers.BUILTIN_SERIALIZERS.setdefault(
            "geojson", 'djorm.contrib.gis.serializers.geojson'
        )
