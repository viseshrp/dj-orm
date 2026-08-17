import os
from unittest import mock

from asgiref.sync import async_to_sync

from djrm.core.exceptions import SynchronousOnlyOperation
from djrm.test import SimpleTestCase
from djrm.utils.asyncio import async_unsafe

from .models import SimpleModel


class DatabaseConnectionTest(SimpleTestCase):
    """A database connection cannot be used in an async context."""

    async def test_get_async_connection(self):
        with self.assertRaises(SynchronousOnlyOperation):
            list(SimpleModel.objects.all())


class AsyncUnsafeTest(SimpleTestCase):
    """
    async_unsafe decorator should work correctly and returns the correct
    message.
    """

    @async_unsafe
    def dangerous_method(self):
        return True

    async def test_async_unsafe(self):
        # async_unsafe decorator catches bad access and returns the right
        # message.
        msg = (
            "You cannot call this from an async context - use a thread or "
            "sync_to_async."
        )
        with self.assertRaisesMessage(SynchronousOnlyOperation, msg):
            self.dangerous_method()

    @mock.patch.dict(os.environ, {"DJANGO_ALLOW_ASYNC_UNSAFE": "true"})
    @async_to_sync  # mock.patch() is not async-aware.
    async def test_async_unsafe_suppressed(self):
        # Decorator doesn't trigger check when the environment variable to
        # suppress it is set.
        try:
            self.dangerous_method()
        except SynchronousOnlyOperation:
            self.fail("SynchronousOnlyOperation should not be raised.")
