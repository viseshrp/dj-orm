# RemovedInDjango60Warning: Remove this entire module.

from djrm.test import SimpleTestCase
from djrm.utils.deprecation import RemovedInDjango60Warning
from djrm.utils.itercompat import is_iterable


class TestIterCompat(SimpleTestCase):
    def test_is_iterable_deprecation(self):
        msg = (
            "djrm.utils.itercompat.is_iterable() is deprecated. "
            "Use isinstance(..., collections.abc.Iterable) instead."
        )
        with self.assertWarnsMessage(RemovedInDjango60Warning, msg) as ctx:
            is_iterable([])
        self.assertEqual(ctx.filename, __file__)
