'\nCaching framework.\n\nThis package defines set of cache backends that all conform to a simple API.\nIn a nutshell, a cache is a set of values -- which can be any object that\nmay be pickled -- identified by string keys.  For the complete API, see\nthe abstract BaseCache class in djorm.core.cache.backends.base.\n\nClient code should use the `cache` variable defined here to access the default\ncache backend and look up non-default cache backends in the `caches` dict-like\nobject.\n\nSee docs/topics/cache.txt for information on the public API.\n'

from djorm.core import signals
from djorm.core.cache.backends.base import (
    BaseCache,
    CacheKeyWarning,
    InvalidCacheBackendError,
    InvalidCacheKey,
)
from djorm.utils.connection import BaseConnectionHandler, ConnectionProxy
from djorm.utils.module_loading import import_string

__all__ = [
    "cache",
    "caches",
    "DEFAULT_CACHE_ALIAS",
    "InvalidCacheBackendError",
    "CacheKeyWarning",
    "BaseCache",
    "InvalidCacheKey",
]

DEFAULT_CACHE_ALIAS = "default"


class CacheHandler(BaseConnectionHandler):
    settings_name = "CACHES"
    exception_class = InvalidCacheBackendError

    def create_connection(self, alias):
        params = self.settings[alias].copy()
        backend = params.pop("BACKEND")
        location = params.pop("LOCATION", "")
        try:
            backend_cls = import_string(backend)
        except ImportError as e:
            raise InvalidCacheBackendError(
                "Could not find backend '%s': %s" % (backend, e)
            ) from e
        return backend_cls(location, params)


caches = CacheHandler()

cache = ConnectionProxy(caches, DEFAULT_CACHE_ALIAS)


def close_caches(**kwargs):
    # Some caches need to do a cleanup at the end of a request cycle. If not
    # implemented in a particular backend cache.close() is a no-op.
    caches.close_all()


signals.request_finished.connect(close_caches)
