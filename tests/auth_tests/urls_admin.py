"""
Test URLs for auth admins.
"""

from djo .contrib import admin 
from djo .contrib .auth .admin import GroupAdmin ,UserAdmin 
from djo .contrib .auth .models import Group ,User 
from djo .contrib .auth .urls import urlpatterns 
from djo .urls import path 

# Create a silo'd admin site for just the user/group admins.
site =admin .AdminSite (name ="auth_test_admin")
site .register (User ,UserAdmin )
site .register (Group ,GroupAdmin )

urlpatterns +=[
path ("admin/",site .urls ),
]
