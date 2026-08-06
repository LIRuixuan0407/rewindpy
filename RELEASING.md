# Releasing RewindPy

1. Ensure `main` is clean and current.
2. Run `python -m pytest -q`.
3. Run `python -m build` and `python -m twine check dist/*`.
4. Confirm `pyproject.toml` and `src/rewindpy/__init__.py` contain the same version.
5. Update `CHANGELOG.md`.
6. Create and push the release tag:

   ```bash
   git tag -a v0.1.0 -m "RewindPy v0.1.0"
   git push origin v0.1.0
   ```

The release workflow builds the wheel and source distribution, checks them, and attaches them to a GitHub Release.
