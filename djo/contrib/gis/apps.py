from djo .apps import AppConfig 
from djo .core import serializers 
from djo .utils .translation import gettext_lazy as _ 


class GISConfig (AppConfig ):
    default_auto_field ="djo.db.models.AutoField"
    name ="djo.contrib.gis"
    verbose_name =_ ("GIS")

    def ready (self ):
        serializers .BUILTIN_SERIALIZERS .setdefault (
        "geojson","djo.contrib.gis.serializers.geojson"
        )
