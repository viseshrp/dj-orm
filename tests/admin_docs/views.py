from djo .contrib .admindocs .middleware import XViewMiddleware 
from djo .http import HttpResponse 
from djo .utils .decorators import decorator_from_middleware 
from djo .views .generic import View 

xview_dec =decorator_from_middleware (XViewMiddleware )


def xview (request ):
    return HttpResponse ()


class XViewClass (View ):
    def get (self ,request ):
        return HttpResponse ()


class XViewCallableObject (View ):
    def __call__ (self ,request ):
        return HttpResponse ()


class CompanyView (View ):
    """
    This is a view for :model:`myapp.Company`
    """

    def get (self ,request ):
        return HttpResponse ()
