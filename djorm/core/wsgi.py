import djorm
from djorm.core.handlers.wsgi import WSGIHandler


def get_wsgi_application():
    "\n    The public interface to Django's WSGI support. Return a WSGI callable.\n\n    Avoids making djorm.core.handlers.WSGIHandler a public API, in case the\n    internal WSGI implementation changes or moves in the future.\n    "
    djorm.setup(set_prefix=False)
    return WSGIHandler()
