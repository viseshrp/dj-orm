from djorm.conf.urls.i18n import i18n_patterns
from djorm.http import HttpResponse, StreamingHttpResponse
from djorm.urls import path
from djorm.utils.translation import gettext_lazy as _

urlpatterns = i18n_patterns(
    path("simple/", lambda r: HttpResponse()),
    path("streaming/", lambda r: StreamingHttpResponse([_("Yes"), "/", _("No")])),
)
