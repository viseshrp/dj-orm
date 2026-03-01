from djo .apps import AppConfig 
from djo .utils .translation import gettext_lazy as _ 


class SessionsConfig (AppConfig ):
    name ="djo.contrib.sessions"
    verbose_name =_ ("Sessions")
