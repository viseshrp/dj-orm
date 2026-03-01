# djo Rebase Workflow

Use this workflow when rebasing the fork onto a new upstream Django 5.2.x tag.

1. Fetch upstream tags and create a fresh branch from the new tag.
2. Re-apply the fork topic commits in order.
3. Run `python3 scripts/rename_namespace.py`.
4. Resolve any remaining conflicts manually, preferring upstream logic with the `djo` namespace.
5. Verify:
   - `python3 scripts/rename_namespace.py --check`
   - `python3 tests/runtests.py --settings=test_sqlite -v0 --parallel`
   - `python3 -c "import djo; print(djo.__version__)"`

Notes:

* `scripts/rename_namespace.py` is the only supported rename workflow.
* The script does not rename `DJANGO_SETTINGS_MODULE`.
* The script intentionally leaves serialization/data strings such as `django-version`
  and translation-domain literals like `django` untouched.
