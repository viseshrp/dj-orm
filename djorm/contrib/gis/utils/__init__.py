"""
This module contains useful utilities for GeoDjango.
"""

from djorm.contrib.gis.utils.ogrinfo import ogrinfo
from djorm.contrib.gis.utils.ogrinspect import mapping, ogrinspect
from djorm.contrib.gis.utils.srs import add_srs_entry
from djorm.core.exceptions import ImproperlyConfigured

__all__ = [
    "add_srs_entry",
    "mapping",
    "ogrinfo",
    "ogrinspect",
]

try:
    # LayerMapping requires DJANGO_SETTINGS_MODULE to be set,
    # and ImproperlyConfigured is raised if that's not the case.
    from djorm.contrib.gis.utils.layermapping import LayerMapError, LayerMapping

    __all__ += ["LayerMapError", "LayerMapping"]

except ImproperlyConfigured:
    pass
