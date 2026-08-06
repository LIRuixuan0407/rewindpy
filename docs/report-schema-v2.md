# RewindPy report schema v2

RewindPy reports are self-contained HTML files. The JSON embedded in the
`rewind-data` script element uses an explicit, versioned contract beginning with
schema v2.

## Required metadata

```json
{
  "schema_version": 2,
  "rewindpy_version": "0.1.1",
  "integrity": {
    "status": "ok",
    "algorithm": "sha256",
    "digest": "...",
    "event_count": 42,
    "source_count": 2,
    "source_line_count": 80
  }
}
```

`schema_version` describes the report-data contract. `rewindpy_version`
describes the generator. They are intentionally separate so that package
releases can remain compatible with the same report schema.

## Canonical source representation

Schema v2 stores each source file as an object:

```json
{
  "sources": {
    "app.py": {
      "encoding": "utf-8",
      "lines": ["def main():", "    raise RuntimeError()"]
    }
  }
}
```

The compatibility layer also accepts legacy source strings, line arrays, and
objects containing `lines`, `source`, or `content`, then converts them to the
canonical representation before the report is written.

## Compatibility behavior

- Missing `schema_version` is treated as legacy schema v1.
- Schema v1 payloads are normalized to schema v2.
- Invalid v2 payloads are rejected at the Python/HTML boundary.
- A report requiring a newer schema displays a bilingual error screen instead
  of leaving the workspace blank or throwing an uncaught JavaScript error.
- Unknown fields are preserved so compatible metadata can be added without
  breaking older readers.

The schema is an internal compatibility contract while RewindPy remains in
alpha. Breaking changes require incrementing `schema_version` and retaining an
explicit migration path for supported older schemas.
