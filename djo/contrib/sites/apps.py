from djo .apps import AppConfig 
from djo .contrib .sites .checks import check_site_id 
from djo .core import checks 
from djo .db .models .signals import post_migrate 
from djo .utils .translation import gettext_lazy as _ 

from .management import create_default_site 


class SitesConfig (AppConfig ):
    default_auto_field ="djo.db.models.AutoField"
    name ="djo.contrib.sites"
    verbose_name =_ ("Sites")

    def ready (self ):
        post_migrate .connect (create_default_site ,sender =self )
        checks .register (check_site_id ,checks .Tags .sites )
