from djo .apps import AppConfig 
from djo .utils .translation import gettext_lazy as _ 


class SiteMapsConfig (AppConfig ):
    default_auto_field ="djo.db.models.AutoField"
    name ="djo.contrib.sitemaps"
    verbose_name =_ ("Site Maps")
