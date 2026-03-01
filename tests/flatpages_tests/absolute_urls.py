from djo .contrib .flatpages import views 
from djo .urls import path 

urlpatterns =[
path ("flatpage/",views .flatpage ,{"url":"/hardcoded/"}),
]
