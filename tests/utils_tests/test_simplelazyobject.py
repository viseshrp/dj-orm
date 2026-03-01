import pickle 

from djo .contrib .auth .models import User 
from djo .test import TestCase 
from djo .utils .functional import SimpleLazyObject 


class TestUtilsSimpleLazyObjectDjangoTestCase (TestCase ):
    def test_pickle (self ):
        user =User .objects .create_user ("johndoe","john@example.com","pass")
        x =SimpleLazyObject (lambda :user )
        pickle .dumps (x )
        # Try the variant protocol levels.
        pickle .dumps (x ,0 )
        pickle .dumps (x ,1 )
        pickle .dumps (x ,2 )
