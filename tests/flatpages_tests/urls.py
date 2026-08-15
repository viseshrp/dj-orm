from djorm.contrib.flatpages.sitemaps import FlatPageSitemap
from djorm.contrib.sitemaps import views
from djorm.urls import include, path

urlpatterns = [
    path(
        "flatpages/sitemap.xml",
        views.sitemap,
        {"sitemaps": {"flatpages": FlatPageSitemap}},
        name='djorm.contrib.sitemaps.views.sitemap',
    ),
    path("flatpage_root/", include('djorm.contrib.flatpages.urls')),
    path("accounts/", include('djorm.contrib.auth.urls')),
]
