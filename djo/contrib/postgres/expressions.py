from djo .contrib .postgres .fields import ArrayField 
from djo .db .models import Subquery 
from djo .utils .functional import cached_property 


class ArraySubquery (Subquery ):
    template ="ARRAY(%(subquery)s)"

    def __init__ (self ,queryset ,**kwargs ):
        super ().__init__ (queryset ,**kwargs )

    @cached_property 
    def output_field (self ):
        return ArrayField (self .query .output_field )
