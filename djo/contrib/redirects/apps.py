from djo .apps import AppConfig 
from djo .utils .translation import gettext_lazy as _ 


class RedirectsConfig (AppConfig ):
    default_auto_field ="djo.db.models.AutoField"
    name ="djo.contrib.redirects"
    verbose_name =_ ("Redirects")
