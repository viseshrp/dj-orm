===
djo
===

``djo`` is Django's ORM, migrations framework, and database backend stack
packaged as a standalone library under the ``djo`` namespace.

It keeps the retained Django public APIs and behavior intact, with one
namespace change:

* ``django.*`` imports become ``djo.*``

What is included
================

* ORM models, fields, querysets, expressions, and managers
* Migration generation and execution
* Built-in database backends
* ``djo.contrib.contenttypes``
* ``djo.contrib.postgres``
* Database-focused management commands such as ``migrate``,
  ``makemigrations``, ``showmigrations``, ``dumpdata``, and ``loaddata``

What is not included
====================

* HTTP, URLs, views, middleware, templates, or forms
* Auth, admin, sessions, messages, staticfiles, sitemaps, or other web-facing
  contrib apps
* Any compatibility ``django`` namespace

Minimal setup
=============

.. code-block:: python

    import djo
    from djo.conf import settings

    settings.configure(
        DATABASES={
            "default": {
                "ENGINE": "djo.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        DEFAULT_AUTO_FIELD="djo.db.models.BigAutoField",
        INSTALLED_APPS=[],
    )
    djo.setup()

For the full fork contract and implementation details, see ``SPEC.md`` and
``IMPLEMENTATION_PLAN.md`` in the repository root.
