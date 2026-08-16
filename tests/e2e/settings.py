import os
from pathlib import Path

BACKEND = os.environ.get("DJRM_E2E_BACKEND", "sqlite")
PASSWORD = "DjrmE2E_2026"


def database_settings(backend: str) -> dict:
    if backend == "sqlite":
        return {
            "ENGINE": "djrm.db.backends.sqlite3",
            "NAME": Path(os.environ.get("DJRM_SQLITE_PATH", "/tmp/djrm-e2e.sqlite3")),
        }
    if backend == "postgresql":
        return {
            "ENGINE": "djrm.db.backends.postgresql",
            "NAME": "djrm",
            "USER": "djrm",
            "PASSWORD": PASSWORD,
            "HOST": os.environ.get("DJRM_POSTGRES_HOST", "127.0.0.1"),
            "PORT": int(os.environ.get("DJRM_POSTGRES_PORT", "35432")),
        }
    if backend == "mysql":
        return {
            "ENGINE": "djrm.db.backends.mysql",
            "NAME": "djrm",
            "USER": "djrm",
            "PASSWORD": PASSWORD,
            "HOST": os.environ.get("DJRM_MYSQL_HOST", "127.0.0.1"),
            "PORT": int(os.environ.get("DJRM_MYSQL_PORT", "33306")),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    if backend == "oracle":
        return {
            "ENGINE": "djrm.db.backends.oracle",
            "NAME": os.environ.get("DJRM_ORACLE_NAME", "127.0.0.1:31521/FREEPDB1"),
            "USER": "DJRM",
            "PASSWORD": PASSWORD,
            "HOST": "",
            "PORT": "",
        }
    raise RuntimeError(f"Unsupported DJRM_E2E_BACKEND: {backend}")


DATABASES = {"default": database_settings(BACKEND)}
DEFAULT_AUTO_FIELD = "djrm.db.models.AutoField"
INSTALLED_APPS = ["e2e.e2e_app"]
SECRET_KEY = "djrm-e2e-secret-key"
USE_TZ = False
