# Browser end-to-end tests

RewindPy's report is a self-contained HTML application, so static string tests are not enough. The browser suite opens a real multi-file report in headless Chromium and verifies:

- source code renders without console or page errors;
- the file explorer and cross-file timeline state stay synchronized;
- `Ctrl+P`, `Ctrl+F`, and `Ctrl+Shift+F` work;
- exception-chain nodes jump to the correct file;
- timeline controls, language switching, and themes update the UI.

Install and run locally:

```bash
python -m pip install -e ".[dev,e2e]"
python -m playwright install chromium
REWINDPY_REQUIRE_BROWSER_E2E=1 python -m pytest -q tests/e2e
```

Without `REWINDPY_REQUIRE_BROWSER_E2E=1`, the test is skipped when a compatible Playwright Chromium binary is unavailable. CI sets the variable so a missing browser is always a failure.
