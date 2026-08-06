# Releasing RewindPy

RewindPy publishes the same verified wheel and source distribution to both GitHub Releases and PyPI. PyPI authentication uses GitHub OIDC Trusted Publishing; no long-lived PyPI token is stored in the repository.

## One-time repository setup

### 1. Create the GitHub environment

In **Settings → Environments**, create an environment named exactly `pypi`.

An approval rule is optional for a personal repository, but recommended. The release workflow only requests `id-token: write` inside this environment-scoped job.

### 2. Register the PyPI Trusted Publisher

Because the `rewindpy` project does not exist on PyPI yet, create a pending publisher from the PyPI account publishing settings:

- PyPI project name: `rewindpy`
- GitHub owner: `LIRuixuan0407`
- Repository: `rewindpy`
- Workflow filename: `release.yml`
- Environment name: `pypi`

The first successful upload creates the PyPI project and converts the pending publisher into a normal trusted publisher.

### 3. Enable GitHub Pages

In **Settings → Pages → Build and deployment**, choose **GitHub Actions** as the source. The `Pages` workflow generates a fresh self-contained report from `main` and deploys it to:

`https://liruixuan0407.github.io/rewindpy/`

## Publish the existing v0.1.0 release to PyPI

After completing the one-time setup, open **Actions → Release → Run workflow** and enter:

```text
v0.1.0
```

The manual run checks out the existing tag, verifies both package version declarations, rebuilds and smoke-tests the distributions, updates the GitHub Release assets, and publishes the same files to PyPI.

## Future release checklist

1. Ensure `main` is clean and current.
2. Update `pyproject.toml` and `src/rewindpy/__init__.py` to the same version.
3. Update both README languages and `CHANGELOG.md`.
4. Run the local verification suite:

   ```bash
   python -m pip install -e ".[dev]"
   python -m ruff check .
   python -m pytest -q
   rewindpy doctor
   rm -rf dist build
   python -m build
   python -m twine check dist/*
   ```

5. Commit and push `main`.
6. Create and push the annotated version tag:

   ```bash
   git tag -a v0.1.1 -m "RewindPy v0.1.1"
   git push origin v0.1.1
   ```

A version tag automatically runs the release workflow. The workflow verifies the tag, runs lint and tests, builds the distributions once, smoke-tests the wheel in a clean environment, attaches the files to a GitHub Release, and publishes them to PyPI with provenance attestations.

PyPI files are immutable. Never delete and recreate a published version; increment the version instead.
