# Contributing to Djo

Djo is a narrow fork of Django's ORM and database stack. Changes should preserve
the retained upstream APIs and keep fork-specific code small.

## Set up

Install [uv](https://docs.astral.sh/uv/) and Git, then run:

```console
git clone git@github.com:YOUR_NAME/djo.git
cd djo
git remote add upstream https://github.com/django/django.git
make install
uv run pre-commit install
```

## Change code

1. Branch from the applicable `djo/<series>-lts` branch.
2. Add a focused regression test to the retained Django suite or
   `tests/djo_smoke`.
3. Run `make check` and `make test`.
4. Update `CHANGELOG.md` for a user-visible Djo change.
5. Open a pull request against the same LTS branch.

Do not add web-framework modules, a `django` compatibility namespace, or new
public convenience APIs without first changing `SPEC.md`.

## Update from Django

Do not merge a Django stable branch into Djo by hand. Follow
[MAINTENANCE.md](MAINTENANCE.md) and use `scripts/apply_django_lts.py` from a
clean source branch. Content conflicts require a file-by-file review so an
upstream security fix is not lost.
