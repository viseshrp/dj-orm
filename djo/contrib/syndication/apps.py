from djo .apps import AppConfig 
from djo .utils .translation import gettext_lazy as _ 


class SyndicationConfig (AppConfig ):
    name ="djo.contrib.syndication"
    verbose_name =_ ("Syndication")
