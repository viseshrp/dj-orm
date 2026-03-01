from djo .apps import AppConfig 
from djo .contrib .staticfiles .checks import check_finders ,check_storages 
from djo .core import checks 
from djo .utils .translation import gettext_lazy as _ 


class StaticFilesConfig (AppConfig ):
    name ="djo.contrib.staticfiles"
    verbose_name =_ ("Static Files")
    ignore_patterns =["CVS",".*","*~"]

    def ready (self ):
        checks .register (check_finders ,checks .Tags .staticfiles )
        checks .register (check_storages ,checks .Tags .staticfiles )
