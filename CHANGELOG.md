# Changelog

This file records djrm-specific changes. Django changes remain documented in the
upstream release notes for the exact tag named by each djrm release.

## Unreleased

### Removed

- Residual SpatiaLite, PostGIS adapter, and Oracle Spatial compatibility hooks
  from the retained ORM and database backend code.
- The GeoDjango roadmap. GIS packages, tests, backends, and native
  integrations are permanently outside djrm's package contract.

### Fixed

- PostgreSQL aggregate and field imports no longer fail because the web-only
  `contrib.postgres.forms` package is absent. PostgreSQL fields now raise the
  documented forms-unavailable error only when `formfield()` is requested.

## [0.1.0] - 2026-08-15

### Added

- A `djrm` distribution with wheel and source-archive builds.
- The first release, based on the exact Django `5.2.17` tag.
- A scripted Django LTS application workflow with resumable conflict handling.
- A manual, `main`-only TestPyPI publishing job; production publishing remains
  gated by a published GitHub release and the protected `pypi` environment.
- CI, release, dependency, contribution, and package verification files derived
  from the sibling `yapc` Cookiecutter.

### Changed

- The distribution, import namespace, and CLI are all named `djrm`.
- Release versions now use SemVer: `0.x` maps to Django 5.2 LTS, `1.x` maps to
  Django 6.2 LTS, and later LTS lines increment the djrm major.
- Removed inherited Django documentation, browser tooling, maintainer scripts,
  and other files outside the standalone ORM project.
- The LTS updater now removes new upstream files that appear inside directories
  intentionally pruned by djrm.
- Removed gettext source catalogs from the package while retaining compiled
  runtime translations.
- Removed orphaned test apps, fixtures, and web-only runner options left after
  the original ORM test-suite pruning.
- Removed the obsolete extraction plan and stale configuration for file types
  and outputs no longer present in the repository.
