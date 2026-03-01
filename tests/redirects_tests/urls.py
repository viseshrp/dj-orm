from djo .http import HttpResponse 
from djo .urls import path 

urlpatterns =[
path ("",lambda req :HttpResponse ("OK")),
]
