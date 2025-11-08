# PyPI Publishing Setup Guide

This guide explains how to publish the Godfather CLI to PyPI using GitHub Actions (Trusted Publishing).

## Prerequisites

✅ Already done:
- Package is built and tested (`python -m build` works)
- `pyproject.toml` is properly configured
- GitHub repository exists

## Step 1: Configure PyPI Trusted Publishing

### 1.1 Register on PyPI

1. Go to https://pypi.org/account/register/
2. Create an account with your email
3. Verify your email address

### 1.2 Add Trusted Publisher on PyPI

1. Go to https://pypi.org/manage/account/publishing/
2. Fill in the form (as shown in your screenshot):
   - **PyPI Project Name**: `godfather-cli`
   - **Owner**: `theaisocietyasu`
   - **Repository name**: `godfather`
   - **Workflow name**: `publish-cli.yml`
   - **Environment name**: `pypi` (optional but recommended)

3. Click "Add"

### 1.3 (Optional) Set up TestPyPI

Repeat the same process at https://test.pypi.org/manage/account/publishing/ for testing:
   - **Environment name**: `testpypi`

## Step 2: Configure GitHub Repository

### 2.1 Create GitHub Environment (Recommended)

1. Go to your GitHub repo settings
2. Navigate to **Environments** → **New environment**
3. Create environment named: `pypi`
4. (Optional) Add protection rules:
   - Required reviewers
   - Deployment branches (only `main` or tags)

### 2.2 Verify Workflow File

The workflow file has been created at `.github/workflows/publish-cli.yml`

Key features:
- ✅ Trusted Publishing (no API tokens needed!)
- ✅ Builds on tag push (`cli-v*.*.*`)
- ✅ Manual trigger option
- ✅ Publishes to both PyPI and TestPyPI

## Step 3: Create a Release

### 3.1 Update Version

Edit `cli/pyproject.toml`:

```toml
version = "1.0.0"  # Update this
```

### 3.2 Create and Push Tag

```bash
cd /home/ash/student_orgs/AIS/godfather

# Commit version change
git add cli/pyproject.toml
git commit -m "Bump CLI version to 1.0.0"
git push

# Create and push tag
git tag cli-v1.0.0
git push origin cli-v1.0.0
```

### 3.3 Monitor the Release

1. Go to https://github.com/theaisocietyasu/godfather/actions
2. Watch the "Publish Godfather CLI to PyPI" workflow run
3. Check https://pypi.org/project/godfather-cli/ after completion

## Step 4: Verify Installation

After successful publication:

```bash
# Install from PyPI
pip install godfather-cli

# Test it
godfather --help
```

## Troubleshooting

### "Project name already exists"

The name `godfather-cli` might be taken. Options:
1. Choose a different name in `pyproject.toml` (e.g., `ais-godfather-cli`)
2. Contact PyPI support to claim the name if it's abandoned

### "No matching distribution found"

- Wait a few minutes after publishing
- Check PyPI project page for the new version
- Try: `pip install --upgrade godfather-cli`

### Workflow fails with "403 Forbidden"

- Ensure Trusted Publisher is configured correctly on PyPI
- Verify the workflow file matches PyPI configuration exactly
- Check that the environment name matches (`pypi`)

## Manual Publishing (Alternative Method)

If you prefer manual publishing:

```bash
cd cli

# Build
python -m build

# Upload (you'll need API token)
pip install twine
twine upload dist/*
```

## Versioning Guidelines

Use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

Examples:
- `1.0.0` → `1.0.1` (bug fix)
- `1.0.1` → `1.1.0` (new feature)
- `1.1.0` → `2.0.0` (breaking change)

Tag format: `cli-v{VERSION}` (e.g., `cli-v1.0.0`)

## Next Release Checklist

- [ ] Update version in `cli/pyproject.toml`
- [ ] Update `cli/README.md` if needed
- [ ] Commit changes
- [ ] Create and push git tag: `git tag cli-v{VERSION}`
- [ ] Push tag: `git push origin cli-v{VERSION}`
- [ ] GitHub Actions will automatically publish
- [ ] Verify on PyPI: https://pypi.org/project/godfather-cli/
- [ ] Test installation: `pip install --upgrade godfather-cli`

## Resources

- **Trusted Publishing**: https://docs.pypi.org/trusted-publishers/
- **PyPI Help**: https://pypi.org/help/
- **GitHub Actions**: https://github.com/pypa/gh-action-pypi-publish
