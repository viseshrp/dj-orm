from djorm.contrib import admin
from djorm.urls import include, path

urlpatterns = [
    path("admin/", include(admin.site.urls)),
]
