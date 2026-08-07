# Multi-file navigation and search

RewindPy reports can contain every project-local source file that contributed to the
captured execution. The report viewer keeps file selection, source position, timeline
step, call stack, value origin, and exception-chain navigation synchronized.

## File explorer

The left sidebar builds a directory tree from the report's `sources` mapping. Each file
shows the number of retained execution events associated with it. Selecting a file jumps
to the event in that file that is closest to the current timeline position.

Paths are normalized in the browser, so reports generated on Windows use the same
navigation behavior as reports generated on Linux or macOS.

## Cross-file navigation

The active source file changes automatically when any of these actions selects an event
in another module:

- moving or playing the execution timeline;
- selecting a call-stack frame;
- selecting an exception-chain node;
- jumping to a value origin;
- selecting a file or a search result.

If the target event is outside the Crash Slice, the viewer switches to **All Events** and
then performs the jump.

## Keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl+P` / `Cmd+P` | Fuzzy-open a captured source file |
| `Ctrl+F` / `Cmd+F` | Search the current source file |
| `Ctrl+Shift+F` / `Cmd+Shift+F` | Search all source, functions, variables, and exceptions |
| `Enter` / `Shift+Enter` | Move to the next or previous current-file match |
| `Esc` | Close search or quick-open overlays |

Quick Open matches both file names and full normalized paths. Global Search results can
point to source text, function calls, captured local-variable names, or exception-chain
messages.

## Built-in demo

Generate a report that crosses three Python modules and contains a three-level exception
chain:

```bash
rewindpy demo multi-file --open
```

The demo captures `app.py`, `service.py`, and `config_loader.py` in a single self-contained
HTML report.
