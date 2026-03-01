from djo .urls import include ,path 

urlpatterns =[
path ("flatpage",include ("djo.contrib.flatpages.urls")),
]
