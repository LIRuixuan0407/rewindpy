# ⏪ RewindPy

**Your Python program crashed. Rewind it.**

RewindPy is an early post-crash time-travel debugger for Python. It records a bounded history of project-local execution events and creates a self-contained HTML report after an uncaught exception.

## MVP features

- Run a script through one CLI command
- Record `call`, `line`, `return`, and `exception` events
- Rewind execution with a timeline
- Inspect source code, locals, and variable changes
- Keep the report local and redact common secret names
- No cloud service and no API key
- Trace likely origins of missing dictionary keys
- Trace where a failing value became `None`
- Focus the timeline with a default Crash Slice view
- Switch back to the complete event history at any time

## Try it

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e .
rewindpy run --output report.html examples/key_error.py
```

The example intentionally crashes. Open `report.html`, then use the slider or arrow keys to rewind the execution.

To see Crash Slice remove a noisy warm-up loop:

```bash
rewindpy run --output crash-slice.html examples/crash_slice.py
```

To trace a value returned as `None`:

```bash
rewindpy run --output none-origin.html examples/none_origin.py
```

To pass arguments to the target script:

```bash
rewindpy run --output report.html path/to/app.py -- --port 8080
```

## Current scope

RewindPy currently targets:

- Python 3.10+
- Single-threaded local scripts
- Uncaught exceptions
- Source files under the target script's directory
- Safely serializable local values and truncated `repr()` fallbacks

It does **not** yet support async task causality, multiprocessing, native extensions, live breakpoints, or deterministic replay.

## Safety

Crash reports may contain sensitive runtime state. RewindPy stores reports locally and redacts variable or dictionary keys containing names such as `password`, `token`, `secret`, and `api_key`. Review a report before sharing it.

## Next milestones

1. Collapse repeated loop events inside the Crash Slice.
2. Trace wrong-type and empty-collection origins.
3. Add report search and stack visualization.
4. Add opt-in VS Code integration after the standalone tracer is useful.

## License

MIT

## Value origin analysis

For `KeyError` crashes, RewindPy scans earlier state changes to find where the missing key disappeared and whether it was probably renamed.

## Crash Slice

Crash reports open in a focused view that keeps the final execution context, traceback checkpoints, propagated exceptions, and the detected value-origin step. Use **All Events** to restore the complete timeline.

## None origin analysis

For errors such as `AttributeError: 'NoneType' object has no attribute ...`, RewindPy identifies the failing local variable, follows a nearby caller assignment, and jumps to the function line that returned `None`.
