<div align="center">

[English](README.md) | [简体中文](README.zh-CN.md)

# ⏪ RewindPy

### Your Python program crashed. Rewind it.

A local, post-crash time-travel debugger for Python.

[![CI](https://github.com/LIRuixuan0407/rewindpy/actions/workflows/ci.yml/badge.svg)](https://github.com/LIRuixuan0407/rewindpy/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/rewindpy.svg)](https://pypi.org/project/rewindpy/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Live Demo](https://img.shields.io/badge/live-demo-8A2BE2)](https://liruixuan0407.github.io/rewindpy/)

</div>

![RewindPy demo](docs/assets/rewindpy-demo.gif)

**[Open the live interactive report](https://liruixuan0407.github.io/rewindpy/)**

RewindPy records a bounded history of project-local Python execution. After an uncaught exception, it writes one self-contained HTML debugging workspace for source code, local values, changes, call stacks, exception causes, and the execution timeline.

## Try it in one minute

```bash
python -m pip install --upgrade rewindpy
rewindpy doctor
rewindpy demo multi-file --open
```

## What v0.2.0 adds

- Navigate every captured source file with a project-style file explorer.
- Follow timeline events, call-stack frames, value origins, and exception causes across files.
- Open files with `Ctrl+P`, search the current file with `Ctrl+F`, and search the whole report with `Ctrl+Shift+F`.
- Inspect explicit `raise ... from ...` causes, implicit exception contexts, `from None`, notes, and nested tracebacks.
- Validate report data through Schema v2 and an embedded SHA-256 integrity digest.
- Exercise the real report UI in Chromium during CI and track report-generation performance.

## Debug your own script

```bash
rewindpy run --open app.py
rewindpy --lang zh run --open app.py
rewindpy run --output crash.html app.py -- --port 8080
```

A crashing target keeps its original non-zero exit code. Reports are local HTML files and do not require a server.

## Report workspace

The report combines:

- a bounded execution timeline with play, pause, step, and speed controls;
- complete captured source files with current, crash, origin, and search highlights;
- local variables and per-step changes;
- a clickable call stack and exception chain;
- Crash Slice, missing-key origin, likely key rename, and `None`-origin analysis;
- English and Simplified Chinese UI, dark/light themes, copy diagnostics, and VS Code source links.

## Built-in demos

```bash
rewindpy demo none-origin --open
rewindpy demo key-error --open
rewindpy demo crash-slice --open
rewindpy demo exception-chain --open
rewindpy demo multi-file --open
```

## pytest integration

```bash
pytest --rewind
pytest --rewind --rewind-dir reports --rewind-lang zh
```

Passing tests do not create reports. Failed-test reports are written to `.rewindpy/` by default, while pytest keeps its normal output and exit code.

## Safe tracing

```bash
rewindpy run --max-events 5000 --include src --exclude tests app.py
rewindpy run --max-events 5000 --max-report-mb 10 app.py
```

RewindPy uses a bounded ring buffer, skips common environment and build directories, compresses repeated loops, preserves crash-critical events, and records retained/discarded statistics.

## Command reference

```text
rewindpy --version
rewindpy --lang auto|en|zh --help
rewindpy doctor [--json]
rewindpy [--lang auto|en|zh] demo [none-origin|key-error|crash-slice|exception-chain|multi-file] [--output FILE] [--open]
rewindpy [--lang auto|en|zh] run SCRIPT [--output FILE] [--max-events N] [--include PATH] [--exclude PATH] [--max-report-mb MB] [--open] [-- ARGS...]
```

## Development and quality gates

```bash
python -m pip install -e ".[dev,e2e]"
python -m ruff check .
python -m pytest -q
python -m playwright install chromium
REWINDPY_REQUIRE_BROWSER_E2E=1 python -m pytest -q tests/e2e
python benchmarks/report_benchmark.py --events 5000 --iterations 3
python scripts/build_live_demo.py --check
rewindpy doctor
```

See [browser testing](docs/browser-e2e.md), [performance](docs/performance.md), [report schema](docs/report-schema-v2.md), [exception chains](docs/exception-chain.md), and [multi-file navigation](docs/multi-file-navigation.md).

## Current scope

RewindPy v0.2.0 targets Python 3.10+, single-threaded local scripts, uncaught exceptions, pytest failures, and Python files under the traced project root.

It is not deterministic replay. It does not yet model async task causality, multiprocessing, native extensions, live breakpoints, or arbitrary mutation inside opaque objects.

## Safety

Crash reports can contain runtime data. RewindPy writes them locally and redacts variable or dictionary keys containing names such as `password`, `token`, `secret`, and `api_key`. Always review a report before sharing it.

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), [RELEASING.md](RELEASING.md), and [CHANGELOG.md](CHANGELOG.md).

## License

RewindPy is licensed under the [MIT License](LICENSE).
