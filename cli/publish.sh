#!/bin/bash

# Godfather CLI Publishing Script
# This script helps you publish the CLI to PyPI

set -e

echo "🚀 Godfather CLI Publisher"
echo "=========================="
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run this from the cli/ directory."
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Install build tools
echo ""
echo "📦 Installing build tools..."
pip install --upgrade build twine

# Clean previous builds
echo ""
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info

# Build the package
echo ""
echo "🔨 Building package..."
python3 -m build

# List built files
echo ""
echo "📦 Built packages:"
ls -lh dist/

echo ""
echo "=========================="
echo "Build complete! 🎉"
echo ""
echo "Next steps:"
echo ""
echo "1. Test the package locally:"
echo "   pip install dist/godfather_cli-*.whl"
echo ""
echo "2. Upload to Test PyPI (optional):"
echo "   twine upload --repository testpypi dist/*"
echo ""
echo "3. Upload to PyPI:"
echo "   twine upload dist/*"
echo ""
echo "Note: You'll need a PyPI account and API token"
echo "Create account at: https://pypi.org/account/register/"
echo "=========================="
