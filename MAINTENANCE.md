# Maintenance and release policy

This document is the source of truth for updating and distributing Djorm.

## Decisions

### Release unit

Djorm follows supported Django LTS lines. It publishes a build for the initial
LTS tag and for every patch or security tag in that LTS line. It does not track
non-LTS Django feature releases.

`main` is the sole long-lived development branch and carries the current LTS
line. The automation creates an isolated candidate branch named
`release/django-<tag>` in a separate local worktree. After the full gate passes,
the candidate tree is merged into `main`; release tags are cut from `main`.

Release tags and distribution versions have four numeric components:

| Django tag | Djorm version | Meaning |
| --- | --- | --- |
| `5.2.17` | `5.2.17.0` | First Djorm build from this exact Django tag |
| `5.2.17` | `5.2.17.1` | Djorm-only rebuild from the same Django tag |
| `6.2` | `6.2.0.0` | First Djorm build from the next LTS feature tag |

The first three components identify the upstream Django source. The fourth is
the Djorm rebuild revision. Pre-release Django tags are never production Djorm
releases.

### Distribution identity

- PyPI distribution: `dj-orm`
- Python import namespace: `djorm`
- Console command: `djorm`
- Repository: `https://github.com/viseshrp/dj-orm`

The `djorm` name on PyPI belongs to an unrelated project, so this repository must
never attempt to publish that distribution name. A release check enforces
`dj-orm` before tagging or publishing.

### Source and support

The `upstream` Git remote must point to `https://github.com/django/django.git`.
Every production candidate starts from an exact upstream tag, not the tip of a
stable branch. This makes the source reproducible and lets users map a Djorm build
to Django security advisories.

Djorm carries the same Python floor and runtime dependency bounds as its upstream
LTS tag unless a retained module requires a documented exception. Optional
database drivers remain user-selected extras.

Support for an LTS line ends when upstream Django ends extended support. An old
Djorm release remains installable, but it does not receive independent security
backports after that date.

### Packaging scaffold

The packaging and automation baseline was rendered from the sibling YAPC
Cookiecutter at commit `df3a78fefc78ffb304dd5a32196e1be7a430bbcb` with
Cookiecutter 2.7.1:

```console
uv run --project ../yapc cookiecutter ../yapc --no-input \
  project_name=djorm \
  project_description="Django ORM, migrations, and database backends as a standalone library." \
  cli_tool=y codecov=y git_init=n github_actions=y
```

The rendered project is a comparison baseline, not an overlay to copy blindly.
Djorm adapts its package name to `dj-orm`, retains the upstream-derived `djorm/`
tree, and scopes formatters to fork-owned files. To adopt a later YAPC version,
render it into a temporary directory, review the infrastructure diff, and
update `yapc_commit` in `.djorm-maintenance.toml`. Routine Django LTS application
does not require rerendering YAPC; the updater applies the reviewed package
infrastructure with the maintained fork delta.

## Mechanical application

Run the tool from a clean Djorm source branch:

```console
uv run python scripts/apply_django_lts.py \
  --django-ref 5.2.17 \
  --output ../djorm-5.2.17
```

The command performs these bounded operations:

1. Fetches the exact tag from the official `upstream` remote and verifies that
   the ref is a final release in the reviewed `lts_series` list in
   `.djorm-maintenance.toml`.
2. Creates `release/django-<tag>` in a separate Git worktree.
3. Regenerates a canonical `djorm` tree for both the recorded upstream base and
   the new tag, then applies their reviewed fork delta with Git's three-way
   merge support.
4. Applies clean additions, edits, and deletions automatically. Reviewed
   packaging and CI files stay fork-owned; incompatible changes in retained
   Django runtime code remain as conflicts for human review.
5. Writes the new upstream provenance and `A.B.C.N` package version, then runs
   the namespace, package, and retained-suite checks.

The source checkout is never switched or rewritten. The tool refuses a dirty
source or output directory that already exists. This tree-delta design keeps
future applications independent of historical package paths and commit names.

### Continue after a semantic conflict

The tool prints the conflicting files and stops. Compare each file with both
the new upstream implementation and the fork change. Prefer the new upstream
logic, then reapply only the ORM-only adjustment.

After resolving and staging every conflict, resume from the source checkout:

```console
uv run python scripts/apply_django_lts.py \
  --continue \
  --output ../djorm-5.2.17
```

Do not use `git checkout --ours` or `--theirs` across all content conflicts.
That can silently discard an upstream security fix or restore a removed web
dependency.

### New LTS series

Use the same command with the final LTS tag, for example `6.2`. The first run is
expected to stop where Django changed retained modules. Resolve those files,
finish the gate, and merge the generated candidate tree into `main`. Before any
later series, add its officially announced series identifier to `lts_series` in
`.djorm-maintenance.toml`; the tool never guesses future LTS numbering. Update
`SPEC.md` only when the retained module contract or supported Python versions
changed.

## Release gate

A candidate can be tagged only when all of these pass:

```console
make check
make test
make build
make check-dist
make inspect-dist
make release-check RELEASE_TAG=v5.2.17.0
```

`make release-check` verifies:

- the Git tag and package version match;
- the version maps to the recorded final Django tag;
- the source is clean and contains no `django` package;
- `dj-orm` is the configured distribution;
- the changelog has a dated entry for the release.

Run `make tag` only from a clean `main` branch that matches its configured
remote. The tag workflow rebuilds and tests the exact tag, then creates a draft
GitHub release with the wheel and source archive. The separate release workflow
publishes those verified files to PyPI only after a maintainer publishes the
GitHub release.

## PyPI setup

Before the first release:

1. Confirm `dj-orm` is still available on PyPI.
2. Add a project-scoped PyPI token as the GitHub environment secret
   `PYPI_TOKEN` in the `pypi` environment.
3. Add a TestPyPI token as `TEST_PYPI_TOKEN` only when an explicit dry run is
   needed. Normal branch pushes do not publish.
4. Protect the `pypi` environment with a required reviewer.

PyPI publication is intentionally separate from ordinary CI. A push to `main`
builds and checks artifacts but cannot publish them.

## Current branch status

`main` was originally forked from a development snapshot nine commits after
Django `5.2.11`, where upstream had already bumped its internal version toward
`5.2.12`. Its package version is therefore a development version and it must not
be tagged as a production build. Generate the first candidate from the latest
final `5.2.x` tag before publishing.
