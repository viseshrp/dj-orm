import djorm
from djorm.core.handlers.asgi import ASGIHandler


def get_asgi_application():
    "\n    The public interface to Django's ASGI support. Return an ASGI 3 callable.\n\n    Avoids making djorm.core.handlers.ASGIHandler a public API, in case the\n    internal implementation changes or moves in the future.\n    "
    djorm.setup(set_prefix=False)
    return ASGIHandler()
