from djorm.urls import include, path

urlpatterns = [
    path("flatpage", include('djorm.contrib.flatpages.urls')),
]
