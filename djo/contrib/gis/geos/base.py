from djo .contrib .gis .geos .error import GEOSException 
from djo .contrib .gis .ptr import CPointerBase 


class GEOSBase (CPointerBase ):
    null_ptr_exception_class =GEOSException 
