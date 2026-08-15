from unittest import mock 

from djorm .db import migrations

try :
    from djorm .contrib .postgres .operations import CryptoExtension
except ImportError :
    CryptoExtension =mock .Mock ()


class Migration (migrations .Migration ):
# Required for the SHA database functions.
    operations =[CryptoExtension ()]
