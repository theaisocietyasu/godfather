#!/bin/bash
# Docker Image Deployment Script
# Builds and pushes the Godfather base image to Docker Hub

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         Godfather Docker Image Deployment Script            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_USERNAME="${DOCKER_USERNAME:-theaisocietyasu}"
DOCKER_IMAGE="godfather-base"
DOCKER_VERSION="${VERSION:-latest}"

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

# Check if we're in the right directory
if [ ! -f "deploy-docker.sh" ]; then
    print_error "Please run this script from the godfather repository root"
    exit 1
fi

# Check Docker
echo "🔍 Checking prerequisites..."
if ! check_command docker; then
    print_error "Docker is required to build and push images"
    echo ""
    echo "Install Docker:"
    echo "  • Ubuntu/Debian: https://docs.docker.com/engine/install/ubuntu/"
    echo "  • macOS: https://docs.docker.com/desktop/install/mac-install/"
    echo "  • Windows: https://docs.docker.com/desktop/install/windows-install/"
    exit 1
fi

# Navigate to docker directory
echo ""
print_info "Navigating to Docker image directory..."
cd docker-images/godfather-base

if [ ! -f "Dockerfile" ]; then
    print_error "Dockerfile not found in docker-images/godfather-base/"
    exit 1
fi

print_success "Found Dockerfile"

# Configuration
echo ""
echo "📝 Current Configuration:"
echo "   Docker Username: $DOCKER_USERNAME"
echo "   Image Name:      $DOCKER_IMAGE"
echo "   Version Tag:     $DOCKER_VERSION"
echo ""

FULL_IMAGE_NAME="$DOCKER_USERNAME/$DOCKER_IMAGE"
FULL_IMAGE_NAME_WITH_TAG="$FULL_IMAGE_NAME:$DOCKER_VERSION"

# Ask if user wants to change configuration
if confirm "Do you want to customize the configuration?"; then
    echo ""
    read -p "Enter Docker Hub username [$DOCKER_USERNAME]: " new_username
    if [ -n "$new_username" ]; then
        DOCKER_USERNAME="$new_username"
        FULL_IMAGE_NAME="$DOCKER_USERNAME/$DOCKER_IMAGE"
        FULL_IMAGE_NAME_WITH_TAG="$FULL_IMAGE_NAME:$DOCKER_VERSION"
    fi
    
    read -p "Enter version tag [$DOCKER_VERSION]: " new_tag
    if [ -n "$new_tag" ]; then
        DOCKER_VERSION="$new_tag"
        FULL_IMAGE_NAME_WITH_TAG="$FULL_IMAGE_NAME:$DOCKER_VERSION"
    fi
    
    echo ""
    print_success "Configuration updated"
    echo "   Full image: $FULL_IMAGE_NAME_WITH_TAG"
fi

# Build the image
echo ""
echo "🔨 Building Docker Image"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_info "Building $FULL_IMAGE_NAME_WITH_TAG..."
echo ""

if docker build -t "$FULL_IMAGE_NAME_WITH_TAG" .; then
    print_success "Image built successfully"
else
    print_error "Failed to build image"
    exit 1
fi

# Also tag as latest if this is a release
echo ""
if [ "$DOCKER_VERSION" != "latest" ]; then
    if confirm "Do you want to also tag this as 'latest'?"; then
        docker tag "$FULL_IMAGE_NAME_WITH_TAG" "$FULL_IMAGE_NAME:latest"
        print_success "Tagged as $FULL_IMAGE_NAME:latest"
    fi
fi

# Show image info
echo ""
echo "📦 Built Images:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker images | head -1
docker images | grep "$DOCKER_IMAGE" | head -5
echo ""

# Show image size
IMAGE_SIZE=$(docker images "$FULL_IMAGE_NAME_WITH_TAG" --format "{{.Size}}")
print_info "Image size: $IMAGE_SIZE"

# Ask about local testing
echo ""
if confirm "Do you want to test the image locally first?"; then
    echo ""
    print_info "Starting interactive test container..."
    echo ""
    echo "You can test the image with the following command:"
    echo ""
    echo "  docker run -it -e GODFATHER_SSH_PUBLIC_KEY=\"\$(cat ~/.ssh/id_rsa.pub)\" $FULL_IMAGE_NAME_WITH_TAG"
    echo ""
    echo "Inside the container, you should see:"
    echo "  • AI Society themed welcome banner"
    echo "  • User workspace in /workspace/users/\$USER"
    echo "  • Shared folder in /workspace/shared"
    echo ""
    
    if confirm "Start test container now?"; then
        echo ""
        docker run -it \
            -e GODFATHER_SSH_PUBLIC_KEY="$(cat ~/.ssh/id_rsa.pub 2>/dev/null || echo 'test-key')" \
            "$FULL_IMAGE_NAME_WITH_TAG"
    else
        print_info "Skipping local test"
    fi
fi

# Check Docker Hub login
echo ""
echo "🔐 Docker Hub Authentication"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_info "Checking Docker Hub authentication..."

if docker info 2>/dev/null | grep -q "Username"; then
    DOCKER_USER=$(docker info 2>/dev/null | grep "Username" | awk '{print $2}')
    print_success "Already logged in as: $DOCKER_USER"
    
    if [ "$DOCKER_USER" != "$DOCKER_USERNAME" ]; then
        print_warning "Logged in as $DOCKER_USER but pushing to $DOCKER_USERNAME"
        if confirm "Do you want to login as $DOCKER_USERNAME?"; then
            docker login
        fi
    fi
else
    print_warning "Not logged in to Docker Hub"
    print_info "Logging in to Docker Hub..."
    echo ""
    docker login
fi

# Push to Docker Hub
echo ""
echo "🚀 Pushing to Docker Hub"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_warning "You are about to push to Docker Hub: $FULL_IMAGE_NAME_WITH_TAG"
echo ""

if confirm "Continue with push?"; then
    # Push the versioned tag
    echo ""
    print_info "Pushing $FULL_IMAGE_NAME_WITH_TAG..."
    if docker push "$FULL_IMAGE_NAME_WITH_TAG"; then
        print_success "Successfully pushed $FULL_IMAGE_NAME_WITH_TAG"
    else
        print_error "Failed to push $FULL_IMAGE_NAME_WITH_TAG"
        exit 1
    fi
    
    # Also push latest if tagged
    if docker images | grep -q "$FULL_IMAGE_NAME.*latest"; then
        echo ""
        print_info "Pushing $FULL_IMAGE_NAME:latest..."
        if docker push "$FULL_IMAGE_NAME:latest"; then
            print_success "Successfully pushed $FULL_IMAGE_NAME:latest"
        else
            print_warning "Failed to push $FULL_IMAGE_NAME:latest"
        fi
    fi
    
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              Docker Image Published! 🎉                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📦 Published Images:"
    echo "   • $FULL_IMAGE_NAME_WITH_TAG"
    if docker images | grep -q "$FULL_IMAGE_NAME.*latest"; then
        echo "   • $FULL_IMAGE_NAME:latest"
    fi
    echo ""
    echo "🔗 Docker Hub URL:"
    echo "   https://hub.docker.com/r/$FULL_IMAGE_NAME"
    echo ""
    echo "💡 Next Steps:"
    echo ""
    echo "   1. Update the default image in the admin portal:"
    echo "      • Edit: frontend/app/dashboard/create-pod/page.tsx"
    echo "      • Change default image to: $FULL_IMAGE_NAME_WITH_TAG"
    echo ""
    echo "   2. Test the image in RunPod:"
    echo "      • Create a new pod in the admin portal"
    echo "      • Use custom image: $FULL_IMAGE_NAME_WITH_TAG"
    echo "      • Connect via CLI: godfather connect"
    echo ""
    echo "   3. Update documentation if needed:"
    echo "      • Update README.md with new image name"
    echo "      • Update deployment guides"
    echo ""
else
    print_warning "Push cancelled"
    echo ""
    print_info "The image is built locally and ready to push when you're ready"
    echo "   To push later, run:"
    echo "   docker push $FULL_IMAGE_NAME_WITH_TAG"
fi

# Return to root directory
cd ../..

echo ""
print_success "Docker deployment script complete!"
