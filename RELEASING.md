# Releasing RewindPy

1. Ensure `main` is clean, current, and all intended changes are listed under the release heading in `CHANGELOG.md`.
2. Confirm `pyproject.toml` and `src/rewindpy/__init__.py` contain the same version.
3. Run the local quality gates:

   ```bash
   python -m pip install -e ".[dev,e2e]"
   python -m ruff check .
   python -m pytest -q
   rewindpy doctor
   python benchmarks/report_benchmark.py --events 5000 --files 4 --iterations 3
   python scripts/build_live_demo.py --check
   ```

4. Run the browser suite after installing Chromium:

   ```bash
   python -m playwright install chromium
   REWINDPY_REQUIRE_BROWSER_E2E=1 python -m pytest -q tests/e2e
   ```

5. Build and inspect the distributions:

   ```bash
   rm -rf build dist
   python -m build
   python -m twine check dist/*
   ```

6. Install the wheel in a clean virtual environment and run `rewindpy --version`, `rewindpy doctor`, and `rewindpy demo multi-file`.
7. Commit and push the release preparation, then wait for the `main` CI run to pass.
8. Create and push the immutable version tag:

   ```bash
   git tag -a v0.2.0 -m "RewindPy v0.2.0"
   git push origin v0.2.0
   ```

The Release workflow verifies the tag, builds and smoke-tests the distributions, creates the GitHub Release, and publishes to PyPI through Trusted Publishing.
