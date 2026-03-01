from djo .apps import AppConfig 
from djo .utils .translation import gettext_lazy as _ 


class AdminDocsConfig (AppConfig ):
    name ="djo.contrib.admindocs"
    verbose_name =_ ("Administrative Documentation")
