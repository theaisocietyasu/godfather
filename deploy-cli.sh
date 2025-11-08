#!/bin/bash
# CLI Deployment Script
# Builds, tests, and publishes the Godfather CLI to PyPI

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              Godfather CLI Deployment Script                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to check command availability
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed"
        return 1
    fi
    print_success "$1 is available"
    return 0
}

# Function to prompt for confirmation
confirm() {
    read -p "$1 (y/n): " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

# Main menu
show_menu() {
    echo ""
    echo "What would you like to do?"
    echo ""
    echo "  1) Build & Publish CLI to PyPI"
    echo "  2) Test CLI locally"
    echo "  3) Build only (no publish)"
    echo "  4) Exit"
    echo ""
    read -p "Enter your choice (1-4): " choice
    echo ""
}

# Build CLI (without publishing)
build_cli() {
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                      Building CLI Package                    ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    # Navigate to CLI directory
    cd cli
    
    # Check if we're in the right place
    if [ ! -f "pyproject.toml" ]; then
        print_error "pyproject.toml not found. Are you in the godfather repository root?"
        exit 1
    fi
    
    # Check Python version
    if ! check_command python3; then
        print_error "Python 3 is required"
        exit 1
    fi
    
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_info "Python version: $python_version"
    
    # Show current version
    current_version=$(grep '^version = ' pyproject.toml | cut -d '"' -f 2)
    print_info "Current version in pyproject.toml: $current_version"
    
    echo ""
    print_info "Installing build tools..."
    pip install --upgrade build twine > /dev/null 2>&1
    print_success "Build tools installed"
    
    # Clean previous builds
    echo ""
    print_info "Cleaning previous builds..."
    rm -rf dist/ build/ *.egg-info
    print_success "Clean complete"
    
    # Build the package
    echo ""
    print_info "Building package..."
    python3 -m build
    print_success "Package built successfully"
    
    # List built files
    echo ""
    echo "📦 Built packages:"
    ls -lh dist/
    echo ""
    
    cd ..
}

# Deploy CLI
deploy_cli() {
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    Deploying CLI to PyPI                     ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    # Navigate to CLI directory
    cd cli
    
    # Check if we're in the right place
    if [ ! -f "pyproject.toml" ]; then
        print_error "pyproject.toml not found. Are you in the godfather repository root?"
        exit 1
    fi
    
    # Check Python version
    if ! check_command python3; then
        print_error "Python 3 is required"
        exit 1
    fi
    
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_info "Python version: $python_version"
    
    # Show current version
    current_version=$(grep '^version = ' pyproject.toml | cut -d '"' -f 2)
    print_info "Current version in pyproject.toml: $current_version"
    echo ""
    
    if confirm "Do you want to update the version number?"; then
        read -p "Enter new version (e.g., 1.0.3): " new_version
        if [ -n "$new_version" ]; then
            sed -i "s/^version = \".*\"/version = \"$new_version\"/" pyproject.toml
            print_success "Version updated to $new_version"
        fi
    fi
    
    echo ""
    print_info "Installing build tools..."
    pip install --upgrade build twine > /dev/null 2>&1
    print_success "Build tools installed"
    
    # Clean previous builds
    echo ""
    print_info "Cleaning previous builds..."
    rm -rf dist/ build/ *.egg-info
    print_success "Clean complete"
    
    # Build the package
    echo ""
    print_info "Building package..."
    python3 -m build
    print_success "Package built successfully"
    
    # List built files
    echo ""
    echo "📦 Built packages:"
    ls -lh dist/
    echo ""
    
    # Ask about testing
    if confirm "Do you want to test the package locally first?"; then
        echo ""
        print_info "Installing package locally..."
        pip install --force-reinstall dist/godfather_cli-*.whl
        print_success "Package installed locally"
        echo ""
        print_info "You can now test with: godfather --help"
        echo ""
        
        if ! confirm "Continue with publishing to PyPI?"; then
            print_warning "Publishing cancelled"
            cd ..
            return
        fi
    fi
    
    # Ask which PyPI to upload to
    echo ""
    echo "Where do you want to publish?"
    echo "  1) Test PyPI (recommended for testing)"
    echo "  2) Production PyPI"
    echo ""
    read -p "Enter your choice (1-2): " pypi_choice
    
    if [ "$pypi_choice" = "1" ]; then
        echo ""
        print_info "Uploading to Test PyPI..."
        twine upload --repository testpypi dist/*
        print_success "Uploaded to Test PyPI!"
        echo ""
        print_info "To install from Test PyPI:"
        echo "  pip install --index-url https://test.pypi.org/simple/ godfather-cli"
    else
        echo ""
        print_warning "You are about to upload to PRODUCTION PyPI"
        if confirm "Are you sure you want to continue?"; then
            print_info "Uploading to PyPI..."
            twine upload dist/*
            print_success "Uploaded to PyPI!"
            echo ""
            print_info "Users can now install with:"
            echo "  pip install godfather-cli"
        else
            print_warning "Publishing cancelled"
        fi
    fi
    
    cd ..
    echo ""
    print_success "CLI deployment complete!"
}

# Test CLI locally
test_cli() {
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    Testing CLI Locally                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    
    cd cli
    
    if [ ! -f "pyproject.toml" ]; then
        print_error "pyproject.toml not found"
        exit 1
    fi
    
    # Build and install
    print_info "Building package..."
    rm -rf dist/ build/ *.egg-info
    python3 -m build > /dev/null 2>&1
    
    print_info "Installing locally..."
    pip install --force-reinstall dist/godfather_cli-*.whl > /dev/null 2>&1
    
    print_success "CLI installed locally!"
    echo ""
    echo "Test commands:"
    echo "  godfather --help"
    echo "  godfather --version"
    echo ""
    
    godfather --help
    
    cd ..
}

# Main script execution
main() {
    # Check if we're in the right directory
    if [ ! -f "deploy-cli.sh" ] || [ ! -d "cli" ]; then
        print_error "Please run this script from the godfather repository root"
        exit 1
    fi
    
    show_menu
    
    case $choice in
        1)
            deploy_cli
            ;;
        2)
            test_cli
            ;;
        3)
            build_cli
            ;;
        4)
            print_info "Exiting..."
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
    
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                      Complete! 🎉                            ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Offer to run again
    if confirm "Do you want to do something else?"; then
        main
    fi
}

# Run main function
main
