#!/bin/bash
# Build and push Godfather base image

set -e

# Configuration
IMAGE_NAME="${DOCKER_USERNAME:-yourdockerhub}/godfather-base"
VERSION="${VERSION:-latest}"

echo "🐳 Building Godfather Base Image"
echo "================================="
echo "Image: $IMAGE_NAME:$VERSION"
echo ""

# Build the image
echo "📦 Building image..."
docker build -t "$IMAGE_NAME:$VERSION" .

echo ""
echo "✅ Build complete!"
echo ""
echo "To test locally:"
echo "  docker run -it -e GODFATHER_SSH_PUBLIC_KEY=\"your-public-key\" $IMAGE_NAME:$VERSION"
echo ""
echo "To push to Docker Hub:"
echo "  docker login"
echo "  docker push $IMAGE_NAME:$VERSION"
echo ""
echo "Then update the image in your Godfather admin panel to:"
echo "  $IMAGE_NAME:$VERSION"
