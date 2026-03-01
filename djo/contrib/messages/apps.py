from djo .apps import AppConfig 
from djo .contrib .messages .storage import base 
from djo .contrib .messages .utils import get_level_tags 
from djo .core .signals import setting_changed 
from djo .utils .functional import SimpleLazyObject 
from djo .utils .translation import gettext_lazy as _ 


def update_level_tags (setting ,**kwargs ):
    if setting =="MESSAGE_TAGS":
        base .LEVEL_TAGS =SimpleLazyObject (get_level_tags )


class MessagesConfig (AppConfig ):
    name ="djo.contrib.messages"
    verbose_name =_ ("Messages")

    def ready (self ):
        setting_changed .connect (update_level_tags )
