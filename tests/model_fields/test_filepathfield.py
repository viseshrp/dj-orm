import os

from djrm.db.models import FilePathField
from djrm.test import SimpleTestCase


class FilePathFieldTests(SimpleTestCase):
    def test_path(self):
        path = os.path.dirname(__file__)
        field = FilePathField(path=path)
        self.assertEqual(field.path, path)

    def test_callable_path(self):
        path = os.path.dirname(__file__)

        def generate_path():
            return path

        field = FilePathField(path=generate_path)
        self.assertEqual(field.path(), path)
