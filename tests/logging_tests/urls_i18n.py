from djo .conf .urls .i18n import i18n_patterns 
from djo .http import HttpResponse 
from djo .urls import path 

urlpatterns =i18n_patterns (
path ("exists/",lambda r :HttpResponse ()),
)
