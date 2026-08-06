# Exception chains

RewindPy records the visible Python exception chain for uncaught failures and
pytest failures. The chain follows Python's traceback rules:

1. An explicit `__cause__` created by `raise NewError(...) from original` wins.
2. Otherwise, an implicit `__context__` is included.
3. A context hidden by `raise ... from None` is not exposed.

The report stores the outermost exception first and the root exception last:

```json
{
  "exception_chain": {
    "items": [
      {
        "index": 0,
        "exception_type": "StartupError",
        "message": "application startup failed",
        "relation_to_next": "cause",
        "file": "app.py",
        "line": 18,
        "function": "start_application",
        "event_step": 27,
        "traceback": [],
        "notes": []
      },
      {
        "index": 1,
        "exception_type": "ValueError",
        "message": "configuration is not valid JSON",
        "relation_to_next": "cause"
      }
    ],
    "truncated": false,
    "cycle_detected": false,
    "max_depth": 16
  }
}
```

Each item keeps its own traceback, project-local source location, optional
PEP 678 notes, and the best matching RewindPy timeline event. Clicking an item
in the report switches to that exception's source and execution step.

## Safety limits

Exception objects can be manually mutated into cycles or extremely long
chains. RewindPy tracks object identity, stops after 16 visible exceptions, and
sets `cycle_detected` or `truncated` instead of hanging report generation.

Exception messages and notes are runtime data. They remain inside the local
self-contained report and should be reviewed before sharing.

## Demo

```bash
rewindpy demo exception-chain --open
```

The demo produces a three-layer explicit chain:

```text
StartupError
└─ caused by ValueError
   └─ caused by JSONDecodeError
```
