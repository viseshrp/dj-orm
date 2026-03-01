from djo .apps import AppConfig 
from djo .utils .translation import gettext_lazy as _ 


class FlatPagesConfig (AppConfig ):
    default_auto_field ="djo.db.models.AutoField"
    name ="djo.contrib.flatpages"
    verbose_name =_ ("Flat Pages")
