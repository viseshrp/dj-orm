import djo 
from djo .core .handlers .wsgi import WSGIHandler 


def get_wsgi_application ():
    """
    The public interface to Django's WSGI support. Return a WSGI callable.

    Avoids making djo.core.handlers.WSGIHandler a public API, in case the
    internal WSGI implementation changes or moves in the future.
    """
    djo .setup (set_prefix =False )
    return WSGIHandler ()
