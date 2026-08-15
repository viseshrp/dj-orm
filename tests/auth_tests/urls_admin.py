"""
Test URLs for auth admins.
"""

from djorm.contrib import admin
from djorm.contrib.auth.admin import GroupAdmin, UserAdmin
from djorm.contrib.auth.models import Group, User
from djorm.contrib.auth.urls import urlpatterns
from djorm.urls import path

# Create a silo'd admin site for just the user/group admins.
site = admin.AdminSite(name="auth_test_admin")
site.register(User, UserAdmin)
site.register(Group, GroupAdmin)

urlpatterns += [
    path("admin/", site.urls),
]
