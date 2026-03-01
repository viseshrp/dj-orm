from djo .contrib .staticfiles import views 
from djo .urls import re_path 

urlpatterns =[
re_path ("^static/(?P<path>.*)$",views .serve ),
]
