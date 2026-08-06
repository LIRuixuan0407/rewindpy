<div align="center">

# ⏪ RewindPy

### Your Python program crashed. Rewind it.

A local, post-crash time-travel debugger for Python.

[![CI](https://github.com/LIRuixuan0407/rewindpy/actions/workflows/ci.yml/badge.svg)](https://github.com/LIRuixuan0407/rewindpy/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

![RewindPy demo](docs/assets/rewindpy-demo.gif)

RewindPy records a bounded history of project-local execution events. When an uncaught exception occurs, it writes a self-contained HTML report that lets you move backward through source lines, local values, and variable changes.

## Try it in one minute

```bash
git clone https://github.com/LIRuixuan0407/rewindpy.git
cd rewindpy
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install .
rewindpy demo --open
```

The built-in demo intentionally crashes, generates `rewindpy-demo.html`, and exits successfully so you can explore the report immediately.

## Debug your own script

```bash
rewindpy run --open app.py
```

Choose the report path and pass arguments to the target program:

```bash
rewindpy run --output crash.html app.py -- --port 8080
```

A crashing target keeps its original non-zero exit code, which makes RewindPy suitable for local scripts and CI reproductions.

## What v0.1.0 can do

- Rewind `call`, `line`, `return`, and `exception` events.
- Inspect source, locals, and per-step value changes.
- Open a focused **Crash Slice** instead of thousands of unrelated events.
- Trace a missing dictionary key back to the step where it disappeared.
- Suggest likely key renames such as `user_id → userid`.
- Trace a `NoneType` crash back to an assignment or function returning `None`.
- Jump directly from the crash to the likely value origin.
- Keep reports local and redact common secret names.

## Built-in demos

```bash
rewindpy demo none-origin --open
rewindpy demo key-error --open
rewindpy demo crash-slice --open
```

## Command reference

```text
rewindpy --version
rewindpy demo [none-origin|key-error|crash-slice] [--output FILE] [--open]
rewindpy run SCRIPT [--output FILE] [--max-events N] [--open] [-- ARGS...]
```

## Current scope

RewindPy v0.1.0 targets Python 3.10+, single-threaded local scripts, uncaught exceptions, and files under the target script's directory.

It is not deterministic replay. It does not yet model async task causality, multiprocessing, native extensions, live breakpoints, or arbitrary mutation inside opaque objects.

## Safety

Crash reports can contain runtime data. RewindPy writes them locally and redacts variable or dictionary keys containing names such as `password`, `token`, `secret`, and `api_key`. Always review a report before sharing it.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m build
python -m twine check dist/*
```

See [RELEASING.md](RELEASING.md) for the release process and [CHANGELOG.md](CHANGELOG.md) for version history.

## License

MIT
