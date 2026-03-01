from djo .conf .urls .i18n import i18n_patterns 
from djo .http import HttpResponse ,StreamingHttpResponse 
from djo .urls import path 
from djo .utils .translation import gettext_lazy as _ 

urlpatterns =i18n_patterns (
path ("simple/",lambda r :HttpResponse ()),
path ("streaming/",lambda r :StreamingHttpResponse ([_ ("Yes"),"/",_ ("No")])),
)
