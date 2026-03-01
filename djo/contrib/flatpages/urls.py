from djo .contrib .flatpages import views 
from djo .urls import path 

urlpatterns =[
path ("<path:url>",views .flatpage ,name ="djo.contrib.flatpages.views.flatpage"),
]
