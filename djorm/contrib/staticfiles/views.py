"""
Views and functions for serving static files. These are only to be used during
development, and SHOULD NOT be used in a production setting.

"""

import os
import posixpath

from djorm.conf import settings
from djorm.contrib.staticfiles import finders
from djorm.http import Http404
from djorm.views import static


def serve(request, path, insecure=False, **kwargs):
    "\n    Serve static files below a given point in the directory structure or\n    from locations inferred from the staticfiles finders.\n\n    To use, put a URL pattern such as::\n\n        from djorm.contrib.staticfiles import views\n\n        path('<path:path>', views.serve)\n\n    in your URLconf.\n\n    It uses the djorm.views.static.serve() view to serve the found files.\n    "
    if not settings.DEBUG and not insecure:
        raise Http404
    normalized_path = posixpath.normpath(path).lstrip("/")
    absolute_path = finders.find(normalized_path)
    if not absolute_path:
        if path.endswith("/") or path == "":
            raise Http404("Directory indexes are not allowed here.")
        raise Http404("'%s' could not be found" % path)
    document_root, path = os.path.split(absolute_path)
    return static.serve(request, path, document_root=document_root, **kwargs)
