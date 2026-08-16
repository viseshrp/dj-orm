FROM python:3.13-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        default-mysql-client \
        pkg-config \
        postgresql-client \
        sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install \
    "asgiref>=3.8.1" \
    "mysqlclient>=2.1.1" \
    "oracledb>=1.3.2" \
    "psycopg[binary]>=3.1.8" \
    "sqlparse>=0.3.1"

CMD ["python", "tests/e2e/run_container.py"]
