import os

BACKEND = os.environ["DJRM_E2E_BACKEND"]
PASSWORD = "DjrmE2E_2026"
ROOT_PASSWORD = "DjrmRootE2E_2026"


def database_settings(alias: str) -> dict:
    suffix = "" if alias == "default" else "_other"
    if BACKEND == "postgresql":
        return {
            "ENGINE": "djrm.db.backends.postgresql",
            "NAME": f"djrm{suffix}",
            "USER": "djrm",
            "PASSWORD": PASSWORD,
            "HOST": os.environ.get("DJRM_POSTGRES_HOST", "postgres"),
            "PORT": int(os.environ.get("DJRM_POSTGRES_PORT", "5432")),
        }
    if BACKEND == "mysql":
        return {
            "ENGINE": "djrm.db.backends.mysql",
            "NAME": f"djrm{suffix}",
            "USER": "root",
            "PASSWORD": ROOT_PASSWORD,
            "HOST": os.environ.get("DJRM_MYSQL_HOST", "mysql"),
            "PORT": int(os.environ.get("DJRM_MYSQL_PORT", "3306")),
            "OPTIONS": {"charset": "utf8mb4"},
            "TEST": {"CHARSET": "utf8mb4", "COLLATION": "utf8mb4_0900_ai_ci"},
        }
    if BACKEND == "oracle":
        test_user = "DJRM_TEST" if alias == "default" else "DJRM_OTHER_TEST"
        return {
            "ENGINE": "djrm.db.backends.oracle",
            "NAME": os.environ.get("DJRM_ORACLE_NAME", "oracle:1521/FREEPDB1"),
            "USER": "SYSTEM",
            "PASSWORD": ROOT_PASSWORD,
            "HOST": "",
            "PORT": "",
            "TEST": {
                "USER": test_user,
                "PASSWORD": PASSWORD,
                "TBLSPACE": f"{test_user}_TS",
                "TBLSPACE_TMP": f"{test_user}_TEMP",
                "DATAFILE": (f"/opt/oracle/oradata/FREE/FREEPDB1/{test_user.lower()}.dbf"),
                "DATAFILE_TMP": (f"/opt/oracle/oradata/FREE/FREEPDB1/{test_user.lower()}_temp.dbf"),
            },
        }
    raise RuntimeError(f"Unsupported DJRM_E2E_BACKEND: {BACKEND}")


DATABASES = {alias: database_settings(alias) for alias in ("default", "other")}
DEFAULT_AUTO_FIELD = "djrm.db.models.AutoField"
SECRET_KEY = "django_tests_secret_key"
USE_TZ = False
