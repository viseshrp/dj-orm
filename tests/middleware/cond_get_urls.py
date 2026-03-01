from djo .http import HttpResponse 
from djo .urls import path 

urlpatterns =[
path ("",lambda request :HttpResponse ("root is here")),
]
