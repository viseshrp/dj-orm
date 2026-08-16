# djrm

[![CI](https://github.com/viseshrp/djrm/actions/workflows/main.yml/badge.svg)](https://github.com/viseshrp/djrm/actions/workflows/main.yml)
[![Python versions](https://img.shields.io/pypi/pyversions/djrm.svg?logo=python&logoColor=white)](https://pypi.org/project/djrm/)
[![Coverage](https://codecov.io/gh/viseshrp/djrm/branch/main/graph/badge.svg)](https://codecov.io/gh/viseshrp/djrm)
[![License: BSD-3-Clause](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](LICENSE)

`djrm` packages Django's ORM, migration framework, and database backends as a
standalone library. It keeps the retained Django APIs under the `djrm` import
namespace and omits the web framework.

This is an independent fork. It is not an official Django Software Foundation
project.

## Installation

The distribution, Python import namespace, and command are all named `djrm`.

```console
python -m pip install djrm
```

Release builds are published to PyPI. See
[Maintenance and releases](#maintenance-and-releases) for the release policy.

## Included

- Models, fields, querysets, managers, expressions, and aggregations
- Schema migrations and data migrations
- SQLite, PostgreSQL, MySQL, and Oracle backends
- `djrm.contrib.contenttypes` and `djrm.contrib.postgres`
- Database-focused commands including `makemigrations`, `migrate`,
  `showmigrations`, `dumpdata`, and `loaddata`

HTTP handling, URL routing, views, middleware, templates, forms, auth, admin,
sessions, static files, GeoDjango, and spatial database support are not included.
The package does not provide a compatibility `django` namespace.

[SPEC.md](SPEC.md) defines the precise compatibility contract, including lazy
form conversion errors, URL-prefix behavior, test-helper limits, logging
fallbacks, and the supported standalone `templatize()` translation helper.

## Minimal setup

```python
import djrm
from djrm.conf import settings

settings.configure(
    DATABASES={
        "default": {
            "ENGINE": "djrm.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
    DEFAULT_AUTO_FIELD="djrm.db.models.BigAutoField",
    INSTALLED_APPS=[],
)
djrm.setup()
```

Commands use the same settings conventions as Django:

```console
export DJANGO_SETTINGS_MODULE=myproject.settings
djrm migrate
python -m djrm showmigrations
```

`DJANGO_SETTINGS_MODULE` keeps its upstream name. Only Python import paths move
from `django.*` to `djrm.*`.

## Development

Install [uv](https://docs.astral.sh/uv/), then run:

```console
make install
make check
make test
make coverage
make test-external
make build
make check-dist
```

`make test` runs the package smoke tests and the retained SQLite ORM suite.
`make coverage` enforces global, modified-runtime, and fork-tooling baselines.
`make test-external` runs migrations and complex ORM queries against disposable
PostgreSQL, MySQL, and Oracle Docker services, exercises SQLite alongside them,
and opens each backend's real command-line client through `djrm dbshell`. It
also verifies that the intentionally unsupported GIS namespace stays absent.
Docker removes the containers, volumes, network, and local runner image when
the test finishes or fails.

## Maintenance and releases

`main` carries the currently supported Django LTS line. Production builds start
from an exact official Django release tag and use SemVer:

```text
Django 5.2.17 -> djrm 0.1.0
Django 6.2    -> djrm 1.0.0
```

djrm `0.x` corresponds to Django 5.2 LTS, `1.x` corresponds to Django 6.2 LTS,
and each later LTS gets the next major. Within an LTS line, a newer Django patch
tag increments the djrm minor; a djrm-only fix from the same tag increments
the patch. The exact Django tag is recorded as release provenance. The update
tool creates a separate worktree, performs the namespace conversion, applies
the reviewed fork tree delta with a three-way merge, and stops for human review
when upstream changed retained code incompatibly. A machine-readable delta
baseline also stops unexpected executable changes, wider byte drift, and new
paths under maintained deletions.

```console
uv run python scripts/apply_django_lts.py \
  --django-ref 5.2.17 \
  --output ../djrm-5.2.17
```

See [MAINTENANCE.md](MAINTENANCE.md) for the branch model, release gate, conflict
workflow, and PyPI setup. [SPEC.md](SPEC.md) defines the retained API.

## License and attribution

The retained Django code remains under Django's BSD 3-Clause license. See
[LICENSE](LICENSE), [LICENSE.python](LICENSE.python), and [AUTHORS](AUTHORS).
Django is a registered trademark of the Django Software Foundation.
