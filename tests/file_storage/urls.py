from djorm.http import HttpResponse
from djorm.urls import path

urlpatterns = [
    path("", lambda req: HttpResponse("example view")),
]
