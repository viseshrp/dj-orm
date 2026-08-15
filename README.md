# djorm

[![CI](https://github.com/viseshrp/dj-orm/actions/workflows/main.yml/badge.svg)](https://github.com/viseshrp/dj-orm/actions/workflows/main.yml)
[![Python versions](https://img.shields.io/pypi/pyversions/dj-orm.svg?logo=python&logoColor=white)](https://pypi.org/project/dj-orm/)
[![Coverage](https://codecov.io/gh/viseshrp/dj-orm/branch/djorm%2F5.2-lts/graph/badge.svg)](https://codecov.io/gh/viseshrp/dj-orm)
[![License: BSD-3-Clause](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](LICENSE)

`djorm` packages Django's ORM, migration framework, and database backends as a
standalone library. It keeps the retained Django APIs under the `djorm` import
namespace and omits the web framework.

This is an independent fork. It is not an official Django Software Foundation
project.

## Installation

The distribution is named `dj-orm` because the unrelated `djorm` project name
is already registered on PyPI. The Python namespace and command remain `djorm`.

```console
python -m pip install dj-orm
```

No production package has been published yet. Builds from the current branch
are development artifacts; see [Maintenance and releases](#maintenance-and-releases).

## Included

- Models, fields, querysets, managers, expressions, and aggregations
- Schema migrations and data migrations
- SQLite, PostgreSQL, MySQL, and Oracle backends
- `djorm.contrib.contenttypes` and `djorm.contrib.postgres`
- Database-focused commands including `makemigrations`, `migrate`,
  `showmigrations`, `dumpdata`, and `loaddata`

HTTP handling, URL routing, views, middleware, templates, forms, auth, admin,
sessions, static files, and other web-facing components are not included. The
package does not provide a compatibility `django` namespace.

## Minimal setup

```python
import djorm
from djorm.conf import settings

settings.configure(
    DATABASES={
        "default": {
            "ENGINE": "djorm.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
    DEFAULT_AUTO_FIELD="djorm.db.models.BigAutoField",
    INSTALLED_APPS=[],
)
djorm.setup()
```

Commands use the same settings conventions as Django:

```console
export DJANGO_SETTINGS_MODULE=myproject.settings
djorm migrate
python -m djorm showmigrations
```

`DJANGO_SETTINGS_MODULE` keeps its upstream name. Only Python import paths move
from `django.*` to `djorm.*`.

## Development

Install [uv](https://docs.astral.sh/uv/), then run:

```console
make install
make check
make test
make build
make check-dist
```

`make test` runs the package smoke tests and the retained SQLite ORM suite.

## Maintenance and releases

Each supported Django LTS line has a Djorm branch such as `djorm/5.2-lts`.
Production builds start from an exact official Django release tag and use a
four-part version:

```text
Django 5.2.17 -> dj-orm 5.2.17.0
```

The final component increments only for a Djorm-only rebuild of the same Django
tag. The update tool creates a separate worktree, performs the namespace
conversion, replays the fork commits, automatically resolves expected deletion
conflicts, and stops for human review when upstream changed retained code.

```console
uv run python scripts/apply_django_lts.py \
  --django-ref 5.2.17 \
  --output ../djorm-5.2.17
```

See [MAINTENANCE.md](MAINTENANCE.md) for the branch model, release gate, conflict
workflow, and PyPI setup. [SPEC.md](SPEC.md) defines the retained API and
[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) records the original extraction.

## License and attribution

The retained Django code remains under Django's BSD 3-Clause license. See
[LICENSE](LICENSE), [LICENSE.python](LICENSE.python), and [AUTHORS](AUTHORS).
Django is a registered trademark of the Django Software Foundation.
