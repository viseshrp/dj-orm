from djo .apps import AppConfig 
from djo .utils .translation import gettext_lazy as _ 


class HumanizeConfig (AppConfig ):
    name ="djo.contrib.humanize"
    verbose_name =_ ("Humanize")
