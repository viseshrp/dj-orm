# RemovedInDjango60Warning: Remove this entire module.

from djo .test import SimpleTestCase 
from djo .utils .deprecation import RemovedInDjango60Warning 
from djo .utils .itercompat import is_iterable 


class TestIterCompat (SimpleTestCase ):
    def test_is_iterable_deprecation (self ):
        msg =(
        "djo.utils.itercompat.is_iterable() is deprecated. "
        "Use isinstance(..., collections.abc.Iterable) instead."
        )
        with self .assertWarnsMessage (RemovedInDjango60Warning ,msg )as ctx :
            is_iterable ([])
        self .assertEqual (ctx .filename ,__file__ )
