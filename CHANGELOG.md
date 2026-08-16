# Changelog

This file records Djorm-specific changes. Django changes remain documented in the
upstream release notes for the exact tag named by each Djorm release.

## Unreleased

## [0.1.0] - 2026-08-15

### Added

- A `dj-orm` distribution with wheel and source-archive builds.
- The first release, based on the exact Django `5.2.17` tag.
- A scripted Django LTS application workflow with resumable conflict handling.
- CI, release, dependency, contribution, and package verification files derived
  from the sibling `yapc` Cookiecutter.

### Changed

- The public distribution name is `dj-orm`; imports and the CLI remain `djorm`.
- Release versions now use SemVer: `0.x` maps to Django 5.2 LTS, `1.x` maps to
  Django 6.2 LTS, and later LTS lines increment the Djorm major.
- Removed inherited Django documentation, browser tooling, maintainer scripts,
  and other files outside the standalone ORM project.
- The LTS updater now removes new upstream files that appear inside directories
  intentionally pruned by Djorm.
- Removed gettext source catalogs from the package while retaining compiled
  runtime translations.
- Removed orphaned test apps, fixtures, and web-only runner options left after
  the original ORM test-suite pruning.
- Removed the obsolete extraction plan and stale configuration for file types
  and outputs no longer present in the repository.
