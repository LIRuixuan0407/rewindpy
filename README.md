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

RewindPy records a bounded history of project-local execution events. When an uncaught exception occurs, it writes a self-contained HTML report that lets you move backward through source lines, local values, and variable changes.

## Try it in one minute

```bash
python -m pip install --upgrade rewindpy
rewindpy doctor
rewindpy demo --open
```

`rewindpy doctor` checks the interpreter, output permissions, and a complete built-in report smoke test. The demo intentionally crashes, generates `rewindpy-demo.html`, and exits successfully so you can explore the report immediately.

## Debug your own script

```bash
rewindpy run --open app.py

# Force Chinese or English output
rewindpy --lang zh run --open app.py
rewindpy --lang en run --open app.py
```

Choose the report path and pass arguments to the target program:

```bash
rewindpy run --output crash.html app.py -- --port 8080
```

A crashing target keeps its original non-zero exit code, which makes RewindPy suitable for local scripts and CI reproductions.

## What v0.1.1 can do

- Rewind `call`, `line`, `return`, and `exception` events.
- Inspect source, locals, and per-step value changes.
- Open a focused **Crash Slice** instead of thousands of unrelated events.
- Trace a missing dictionary key back to the step where it disappeared.
- Suggest likely key renames such as `user_id → userid`.
- Trace a `NoneType` crash back to an assignment or function returning `None`.
- Jump directly from the crash to the likely value origin.
- Keep reports local and redact common secret names.

## Safe tracing

```bash
rewindpy run --max-events 5000 --include src --exclude tests app.py
```

RewindPy keeps the newest events in a bounded ring buffer, preserves the crash tail, skips common environment/build directories by default, and shows retained/discarded event statistics in the report. Both `--include` and `--exclude` may be repeated.

### Safe Tracing: report-size protection

```bash
rewindpy run --max-events 5000 --max-report-mb 10 app.py
```

RewindPy compresses repeated loops and prioritizes crash slices, exception events, and value origins when a report exceeds its budget.

## pytest integration

After installing RewindPy in your test environment, generate a local report for every failed test:

```bash
pytest --rewind
pytest --rewind --rewind-dir reports --rewind-lang zh
```

Passing tests do not create reports. Failed-test reports are written to `.rewindpy/` by default, while pytest keeps its original output and exit code.

## Built-in demos

```bash
rewindpy demo none-origin --open
rewindpy demo key-error --open
rewindpy demo crash-slice --open
```

## Command reference

```text
rewindpy --version
rewindpy --lang zh --help
rewindpy doctor [--json]
rewindpy [--lang auto|en|zh] demo [none-origin|key-error|crash-slice] [--output FILE] [--open]
rewindpy [--lang auto|en|zh] run SCRIPT [--output FILE] [--max-events N] [--open] [-- ARGS...]
```

The CLI auto-detects Chinese locales. You can also set `REWINDPY_LANG=zh` or use `--lang zh`. Generated reports include an `EN / 中文` switch.

## Current scope

RewindPy v0.1.1 targets Python 3.10+, single-threaded local scripts, uncaught exceptions, and files under the target script's directory.

It is not deterministic replay. It does not yet model async task causality, multiprocessing, native extensions, live breakpoints, or arbitrary mutation inside opaque objects.

## Safety

Crash reports can contain runtime data. RewindPy writes them locally and redacts variable or dictionary keys containing names such as `password`, `token`, `secret`, and `api_key`. Always review a report before sharing it.

## Development

```bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m pytest -q
rewindpy doctor
python -m build
python -m twine check dist/*
```

See [CONTRIBUTING.md](CONTRIBUTING.md) to contribute, [SECURITY.md](SECURITY.md) for private vulnerability reporting, [RELEASING.md](RELEASING.md) for the release process, and [CHANGELOG.md](CHANGELOG.md) for version history.

## License

RewindPy is licensed under the [MIT License](LICENSE).
