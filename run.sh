#!/bin/bash

# Exit on error
set -e

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_IMAGE_NAME="biohackathon-einburgh:latest"
CONTAINER_NAME="biohackathon-app"
STREAMLIT_PORT=8501

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Building Docker image...${NC}"

# Build the Docker image
docker build --platform linux/amd64 -t "$DOCKER_IMAGE_NAME" -f .devcontainer/Dockerfile "$PROJECT_ROOT"

echo -e "${BLUE}Stopping any existing containers...${NC}"

# Stop and remove existing container if it exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
fi

echo -e "${GREEN}Starting Streamlit app...${NC}"
echo -e "${GREEN}Access the app at: http://localhost:${STREAMLIT_PORT}${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the container${NC}\n"

# Run the Docker container with mounted volumes
docker run \
    --name "$CONTAINER_NAME" \
    --platform linux/amd64 \
    -it \
    --rm \
    -p "$STREAMLIT_PORT:8501" \
    -v "$PROJECT_ROOT:/app/" \
    -e STREAMLIT_SERVER_PORT=8501 \
    -e STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    "$DOCKER_IMAGE_NAME" \
    /bin/bash
