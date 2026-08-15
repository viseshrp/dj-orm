from djorm.contrib.staticfiles import views
from djorm.urls import re_path

urlpatterns = [
    re_path("^static/(?P<path>.*)$", views.serve),
]
