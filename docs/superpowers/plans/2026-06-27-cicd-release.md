# CI/CD Release Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a GitHub Actions release workflow that builds and publishes `gnome-monitor-mirror` to PyPI and creates a GitHub Release whenever a `v*.*.*` tag is pushed.

**Architecture:** A single new workflow file (`.github/workflows/release.yml`) triggered by version tags. It validates that the tag matches `pyproject.toml`, builds the dist artifacts with `python -m build`, publishes to PyPI via OIDC Trusted Publishing (no secret tokens), then creates a GitHub Release with the artifacts attached.

**Tech Stack:** GitHub Actions, `pypa/gh-action-pypi-publish@release/v1`, `softprops/action-gh-release@v2`, `python -m build`

## Global Constraints

- Python minimum: 3.7 (per `pyproject.toml`); use Python 3.11 in CI for building
- PyPI package name: `gnome-monitor-mirror`
- GitHub repo: `Toxica20002/gmm`
- Workflow file MUST be named `release.yml` (PyPI trusted publisher is registered against this exact filename)
- Do NOT modify `.github/workflows/ci.yml`
- Tag format: `v` followed by semver — e.g. `v0.2.0` (enforced by `on.push.tags` filter)

---

### Task 1: Create the release workflow

**Files:**
- Create: `.github/workflows/release.yml`

**Interfaces:**
- Consumes: `pyproject.toml` (reads `version` field to validate against the pushed tag)
- Produces: PyPI release of `gnome-monitor-mirror`, GitHub Release with `dist/*.whl` and `dist/*.tar.gz` attached

- [ ] **Step 1: Create `.github/workflows/release.yml`**

```yaml
name: Release

on:
  push:
    tags:
      - "v*.*.*"

permissions:
  contents: write   # needed to create GitHub Release
  id-token: write   # needed for PyPI OIDC trusted publishing

jobs:
  release:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Validate version matches tag
        run: |
          TAG="${GITHUB_REF_NAME#v}"
          TOML_VERSION=$(grep '^version' pyproject.toml | head -1 | sed 's/.*= *"\(.*\)"/\1/')
          echo "Tag version:   $TAG"
          echo "TOML version:  $TOML_VERSION"
          if [ "$TAG" != "$TOML_VERSION" ]; then
            echo "ERROR: Tag v$TAG does not match pyproject.toml version $TOML_VERSION"
            echo "Bump version in pyproject.toml before tagging."
            exit 1
          fi

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install build tools
        run: pip install build

      - name: Build
        run: python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: dist/*
          generate_release_notes: true
```

- [ ] **Step 2: Lint the workflow YAML locally**

```bash
# If actionlint is available:
actionlint .github/workflows/release.yml

# Otherwise, validate YAML is well-formed:
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))" && echo "YAML OK"
```

Expected: no errors. If `actionlint` flags `GITHUB_REF_NAME` or `softprops/action-gh-release`, those are false positives — both are standard.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "ci: add release workflow for PyPI and GitHub Releases"
```

---

### Task 2: One-time PyPI Trusted Publisher setup

This is a manual step done once on pypi.org. No code changes.

- [ ] **Step 1: Create the PyPI project (if it doesn't exist yet)**

  Go to https://pypi.org and log in as the package owner. If `gnome-monitor-mirror` has never been published, the first trusted-publisher push creates it automatically — skip to Step 2.

- [ ] **Step 2: Register the trusted publisher**

  On pypi.org → Account Settings → **Publishing** → **Add a new pending publisher**, fill in:

  | Field | Value |
  |-------|-------|
  | PyPI project name | `gnome-monitor-mirror` |
  | Owner | `Toxica20002` |
  | Repository name | `gmm` |
  | Workflow filename | `release.yml` |
  | Environment name | *(leave blank)* |

  Click **Add**. No token is created.

- [ ] **Step 3: Verify no `PYPI_TOKEN` secret exists**

  On github.com → `Toxica20002/gmm` → Settings → Secrets and variables → Actions. If a `PYPI_TOKEN` secret exists, delete it — it conflicts with OIDC publishing.

---

### Task 3: Ship the first release

- [ ] **Step 1: Bump version in `pyproject.toml`**

  Change `version = "0.1.0"` to the desired release version (e.g. `"0.1.1"` for a patch, `"0.2.0"` for a minor bump).

- [ ] **Step 2: Commit the version bump**

```bash
git add pyproject.toml
git commit -m "chore: bump version to 0.2.0"
```

- [ ] **Step 3: Tag and push**

```bash
git tag v0.2.0
git push origin main --tags
```

- [ ] **Step 4: Verify the Actions run**

  Go to github.com → `Toxica20002/gmm` → Actions → **Release** workflow. All steps should be green.

  Expected:
  - "Validate version matches tag" → passes
  - "Build" → produces `dist/gnome_monitor_mirror-0.2.0-py3-none-any.whl` and `.tar.gz`
  - "Publish to PyPI" → `gnome-monitor-mirror 0.2.0` visible on pypi.org
  - "Create GitHub Release" → release appears at github.com/Toxica20002/gmm/releases with artifacts attached

- [ ] **Step 5: Smoke-test the PyPI install**

```bash
pip install gnome-monitor-mirror==0.2.0
gmm --help
```

  Expected: help output prints, no import errors.
