from unittest import mock 

from djo .db import migrations 

try :
    from djo .contrib .postgres .operations import CryptoExtension 
except ImportError :
    CryptoExtension =mock .Mock ()


class Migration (migrations .Migration ):
# Required for the SHA database functions.
    operations =[CryptoExtension ()]
