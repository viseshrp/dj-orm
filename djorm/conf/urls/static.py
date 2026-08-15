import re
from urllib.parse import urlsplit

from djorm.conf import settings
from djorm.core.exceptions import ImproperlyConfigured
from djorm.urls import re_path
from djorm.views.static import serve


def static(prefix, view=serve, **kwargs):
    '\n    Return a URL pattern for serving files in debug mode.\n\n    from djorm.conf import settings\n    from djorm.conf.urls.static import static\n\n    urlpatterns = [\n        # ... the rest of your URLconf goes here ...\n    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)\n    '
    if not prefix:
        raise ImproperlyConfigured("Empty static prefix not permitted")
    elif not settings.DEBUG or urlsplit(prefix).netloc:
        # No-op if not in debug mode or a non-local prefix.
        return []
    return [
        re_path(
            r"^%s(?P<path>.*)$" % re.escape(prefix.lstrip("/")), view, kwargs=kwargs
        ),
    ]
