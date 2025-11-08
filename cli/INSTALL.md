# Godfather CLI - Installation Guide

## For End Users

### Quick Install (Recommended)

Install directly from GitHub:

```bash
pip install git+https://github.com/theaisocietyasu/godfather.git#subdirectory=cli
```

That's it! Now run:
```bash
godfather
```

### Verify Installation

```bash
# Check if installed
godfather --help

# Check version
pip show godfather-cli
```

### Updating

To update to the latest version:

```bash
pip install --upgrade git+https://github.com/theaisocietyasu/godfather.git#subdirectory=cli
```

### Uninstalling

```bash
pip uninstall godfather-cli
```

---

## For Developers/Contributors

### Setting Up Development Environment

1. Clone the repository:
```bash
git clone https://github.com/theaisocietyasu/godfather.git
cd godfather/cli
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in editable mode:
```bash
pip install -e .
```

Now any changes you make to the code will be immediately reflected when you run `godfather`.

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests (when available)
pytest tests/
```

### Building for Distribution

```bash
# Use the publish script
./publish.sh

# Or manually:
pip install build
python -m build
```

---

## For Administrators (Publishing to PyPI)

### First-Time Setup

1. Create a PyPI account at https://pypi.org/account/register/
2. Generate an API token at https://pypi.org/manage/account/token/
3. Configure the token:
```bash
# Create or edit ~/.pypirc
cat > ~/.pypirc << EOF
[pypi]
  username = __token__
  password = pypi-YOUR_TOKEN_HERE
EOF
chmod 600 ~/.pypirc
```

### Publishing a New Version

1. Update version in `pyproject.toml`:
```toml
version = "1.0.1"  # Increment this
```

2. Build and publish:
```bash
cd cli
./publish.sh
twine upload dist/*
```

3. Users can now install with:
```bash
pip install godfather-cli
```

### Publishing to Test PyPI First (Recommended)

Before publishing to the real PyPI, test on Test PyPI:

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ godfather-cli
```

---

## Troubleshooting

### "Command not found: godfather"

Make sure the pip bin directory is in your PATH:

```bash
# On Linux/Mac
export PATH="$HOME/.local/bin:$PATH"

# On Windows (PowerShell)
$env:PATH += ";$env:USERPROFILE\AppData\Local\Programs\Python\Python311\Scripts"
```

### "Module not found" errors

Reinstall the package:

```bash
pip uninstall godfather-cli
pip install --force-reinstall git+https://github.com/theaisocietyasu/godfather.git#subdirectory=cli
```

### Rich library not displaying colors

Some terminals don't support colors. Try:

```bash
# Force color output
export FORCE_COLOR=1
godfather
```

---

## System Requirements

- **Python**: 3.7 or higher
- **Operating Systems**: 
  - ✅ Linux
  - ✅ macOS  
  - ✅ Windows 10/11
- **Dependencies**:
  - requests >= 2.25.0
  - rich >= 13.0.0

---

## Additional Resources

- **Documentation**: See the main [README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/theaisocietyasu/godfather/issues)
- **Source Code**: [GitHub Repository](https://github.com/theaisocietyasu/godfather)
