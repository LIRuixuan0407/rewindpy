# Changelog

All notable changes to RewindPy are documented here.

## [Unreleased]

## [0.1.1] - 2026-08-06

### Added

- PyPI Trusted Publishing through GitHub Actions and short-lived OIDC credentials.
- A GitHub Pages workflow that generates and deploys a fresh interactive demo from `main`.
- Manual publication of an existing release tag, including the first `v0.1.0` PyPI upload.
- Installed-wheel report generation checks on both Linux and Windows CI runners.
- Safe tracing with a bounded ring buffer and discarded-event statistics.
- Repeatable `--include` and `--exclude` path filters.
- Trace statistics in bilingual crash reports.
- English and Simplified Chinese CLI, crash-report UI, and README documentation.
- `--lang auto|en|zh` and `REWINDPY_LANG` language selection.
- `rewindpy doctor` environment and end-to-end report diagnostics.
- Contributor, security, issue, and pull-request guidance in both languages.
- Ruff linting and built-wheel smoke testing in CI.

### Changed

- Redesigned the crash report with a fixed application shell and a product-focused visual system.
- Fixed timeline dragging so only the source panel scrolls and the page no longer jumps vertically.
- Replaced separate English and Chinese controls with one fixed-width language toggle.
- Split release automation into isolated build, GitHub Release, and PyPI publishing jobs.
- Updated the quick start to install the public package directly from PyPI.

## [0.1.0] - 2026-08-06

### Added

- Post-crash HTML timeline for project-local Python execution.
- Crash Slice view that focuses on the execution path nearest the failure.
- Missing dictionary-key origin analysis with likely rename detection.
- `NoneType` origin analysis that follows values back to assignments or function returns.
- Local secret redaction and bounded event recording.
- Built-in `rewindpy demo` command for a zero-setup first run.
- Python package metadata, CI, release automation, and release documentation.
- `pytest --rewind` integration for generating one local report per failed test.
- `--rewind-dir`, `--rewind-max-events`, `--rewind-max-report-mb`, and `--rewind-lang` options.
