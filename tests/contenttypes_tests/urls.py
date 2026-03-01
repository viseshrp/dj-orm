from djo .contrib .contenttypes import views 
from djo .urls import re_path 

urlpatterns =[
re_path (r"^shortcut/([0-9]+)/(.*)/$",views .shortcut ),
]
