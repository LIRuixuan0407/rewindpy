# Releasing RewindPy

1. Ensure `main` is clean and current.
2. Run `python -m ruff check .`, `python -m pytest -q`, and `rewindpy doctor`.
3. Run `python -m build` and `python -m twine check dist/*`.
4. Install the generated wheel in a clean virtual environment and run `rewindpy --lang zh doctor`.
5. Confirm `pyproject.toml` and `src/rewindpy/__init__.py` contain the same version.
6. Update both README languages and `CHANGELOG.md`.
7. Create and push the release tag:

   ```bash
   git tag -a v0.1.0 -m "RewindPy v0.1.0"
   git push origin v0.1.0
   ```

The release workflow builds the wheel and source distribution, checks them, and attaches them to a GitHub Release.
