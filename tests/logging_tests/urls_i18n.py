from djorm.conf.urls.i18n import i18n_patterns
from djorm.http import HttpResponse
from djorm.urls import path

urlpatterns = i18n_patterns(
    path("exists/", lambda r: HttpResponse()),
)
