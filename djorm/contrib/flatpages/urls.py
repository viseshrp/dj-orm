from djorm.contrib.flatpages import views
from djorm.urls import path

urlpatterns = [
    path("<path:url>", views.flatpage, name='djorm.contrib.flatpages.views.flatpage'),
]
