# CI/CD Release Pipeline — Design Spec

**Date:** 2026-06-27
**Project:** gmm (gnome-monitor-mirror)
**Repo:** https://github.com/Toxica20002/gmm

---

## Goal

Automate building and publishing a new release with a single `git push --tags`. No manual artifact uploads, no PyPI token secrets to rotate.

---

## Trigger

Push any tag matching `v*.*.*` (e.g. `v0.2.0`).

The existing `ci.yml` runs on every push/PR and is not modified.

---

## Workflow: `.github/workflows/release.yml`

### Steps

1. **Checkout** — full git history (`fetch-depth: 0`) so tag context is available.

2. **Validate version sync** — extract `version` from `pyproject.toml` and assert it equals the tag (without the `v` prefix). Fail with a clear message if they diverge. Prevents publishing stale version numbers.

3. **Set up Python** — Python 3.11, cache pip.

4. **Install build tools** — `pip install build`.

5. **Build** — `python -m build` → produces `dist/*.whl` and `dist/*.tar.gz`.

6. **Publish to PyPI** — via OIDC Trusted Publishing (`pypa/gh-action-pypi-publish`). No `PYPI_TOKEN` secret needed. Requires a one-time setup on pypi.org (see Setup section below).

7. **Create GitHub Release** — `softprops/action-gh-release` creates a release from the tag, attaches the `dist/` artifacts, and auto-generates release notes from git log since the previous tag.

### Permissions

The workflow requires:
```yaml
permissions:
  contents: write   # create GitHub Release
  id-token: write   # OIDC token for PyPI trusted publishing
```

---

## One-Time PyPI Setup

Before the first release, configure Trusted Publishing on pypi.org:

1. Create the project `gnome-monitor-mirror` on pypi.org (first publish creates it automatically with trusted publishing, or create manually).
2. Go to **pypi.org → Account → Publishing → Add a new pending publisher**.
3. Fill in:
   - PyPI project name: `gnome-monitor-mirror`
   - GitHub owner: `Toxica20002`
   - GitHub repo: `gmm`
   - Workflow filename: `release.yml`
   - Environment: *(leave blank)*

No secret tokens are created or stored anywhere.

---

## Release Workflow (Day-to-Day)

```bash
# 1. Bump version in pyproject.toml
#    e.g. change version = "0.1.0" to version = "0.2.0"

# 2. Commit
git add pyproject.toml
git commit -m "chore: bump version to 0.2.0"

# 3. Tag and push
git tag v0.2.0
git push origin main --tags
```

GitHub Actions fires, builds, publishes to PyPI, and creates a GitHub Release automatically.

---

## Files Changed

| File | Change |
|------|--------|
| `.github/workflows/release.yml` | New — release pipeline |
| `.github/workflows/ci.yml` | No change |

---

## Out of Scope

- Automated version bumping (user bumps `pyproject.toml` manually before tagging)
- CHANGELOG generation (GitHub auto-notes from git log is sufficient for now)
- TestPyPI dry-run stage (add later if needed)
