from djo .contrib import admin 
from djo .urls import include ,path 

urlpatterns =[
path ("admin/",include (admin .site .urls )),
]
