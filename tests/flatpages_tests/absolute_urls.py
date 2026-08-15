from djorm.contrib.flatpages import views
from djorm.urls import path

urlpatterns = [
    path("flatpage/", views.flatpage, {"url": "/hardcoded/"}),
]
