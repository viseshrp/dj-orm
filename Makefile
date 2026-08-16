SHELL := bash
.SHELLFLAGS := -euo pipefail -c

.PHONY: install
install: ## Install the locked development environment
	@if [ -f uv.lock ]; then \
		uv sync --frozen --reinstall-package djrm; \
	else \
		uv sync --reinstall-package djrm; \
	fi

.PHONY: check
check: ## Check the lockfile and maintained project files
	uv lock --check
	uv run pre-commit run --all-files
	uv run python scripts/check_path_case.py
	uv run python scripts/audit_upstream_delta.py

.PHONY: test-smoke
test-smoke: install ## Run package and maintenance-tool smoke tests
	uv run python -m pytest tests/djrm_smoke

.PHONY: test-upstream
test-upstream: ## Run the retained ORM suite with SQLite
	uv run python tests/runtests.py --settings=test_sqlite -v0 --parallel=1

.PHONY: test
test: test-smoke test-upstream ## Run all local tests

.PHONY: test-external
test-external: ## Run Docker-backed SQLite, PostgreSQL, MySQL, and Oracle E2E tests
	uv run python scripts/test_external_databases.py

.PHONY: coverage
coverage: ## Run the retained suite with coverage data
	uv run coverage erase
	uv run coverage run tests/runtests.py --settings=test_sqlite -v0 --parallel=1
	uv run coverage xml

.PHONY: test-matrix
test-matrix: ## Run tox across supported Python versions
	uv run tox

.PHONY: clean-dist
clean-dist: ## Remove only built distribution artifacts
	rm -rf dist

.PHONY: build
build: clean-dist ## Build wheel and source archive from an empty artifact directory
	uv build

.PHONY: check-dist
check-dist: ## Validate package metadata and long description
	uv run twine check dist/*

.PHONY: inspect-dist
inspect-dist: ## Check package contents and install the wheel in isolation
	uv run python scripts/inspect_dist.py dist

.PHONY: release-check
release-check: ## Verify release provenance and version
	uv run python scripts/check_release.py --tag "$(RELEASE_TAG)"

.PHONY: tag
tag: ## Create and push a verified release tag
	bash scripts/tag_release.sh

.PHONY: publish
publish: ## Publish verified artifacts to PyPI
	uv publish --publish-url=https://upload.pypi.org/legacy/ --no-cache

.PHONY: publish-test
publish-test: ## Publish verified artifacts to TestPyPI
	uv publish --publish-url=https://test.pypi.org/legacy/ --no-cache

.PHONY: clean
clean: ## Remove generated build and test artifacts
	rm -rf build dist .coverage coverage.xml coverage-html .pytest_cache

.PHONY: help
help:
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "%-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help
