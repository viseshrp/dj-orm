from djorm.http import HttpResponse
from djorm.urls import path

urlpatterns = [
    path("", lambda request: HttpResponse("root is here")),
]
