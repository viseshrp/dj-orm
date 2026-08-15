from djorm.contrib.gis.geos.error import GEOSException
from djorm.contrib.gis.ptr import CPointerBase


class GEOSBase(CPointerBase):
    null_ptr_exception_class = GEOSException
