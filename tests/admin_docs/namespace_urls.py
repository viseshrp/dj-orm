from djorm.contrib import admin
from djorm.urls import include, path

from . import views

backend_urls = (
    [
        path("something/", views.XViewClass.as_view(), name="something"),
    ],
    "backend",
)

urlpatterns = [
    path("admin/doc/", include('djorm.contrib.admindocs.urls')),
    path("admin/", admin.site.urls),
    path("api/backend/", include(backend_urls, namespace="backend")),
]
