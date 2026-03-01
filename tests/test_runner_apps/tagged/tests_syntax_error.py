from unittest import TestCase 

from djo .test import tag 


@tag ('syntax_error')
class SyntaxErrorTestCase (TestCase ):
    pass 


1 syntax_error # NOQA
