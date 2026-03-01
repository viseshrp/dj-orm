import os 

from djo .contrib .contenttypes .models import ContentType 
from djo .test import TestCase ,override_settings 
from djo .utils import translation 


@override_settings (
USE_I18N =True ,
LOCALE_PATHS =[
os .path .join (os .path .dirname (__file__ ),"locale"),
],
LANGUAGE_CODE ="en",
LANGUAGES =[
("en","English"),
("fr","French"),
],
)
class ContentTypeTests (TestCase ):
    def test_verbose_name (self ):
        company_type =ContentType .objects .get (app_label ="i18n",model ="company")
        with translation .override ("en"):
            self .assertEqual (str (company_type ),"I18N | Company")
        with translation .override ("fr"):
            self .assertEqual (str (company_type ),"I18N | Société")
