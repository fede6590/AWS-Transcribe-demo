#!/bin/bash

# Prompt for AWS credentials
read -p "Enter your AWS Access Key ID: " AWS_ACCESS_KEY_ID
read -sp "Enter your AWS Secret Access Key: " AWS_SECRET_ACCESS_KEY
echo
read -sp "Enter your AWS Session Token (if you have one): " AWS_SESSION_TOKEN
echo

# Prompt for the source URL or local path
read -p "Enter the source URL or local path: " SOURCE

### FFMPEG FLAGS
LOGLEVEL="warning"  # debug, info, warning (default param), fatal
VERBOSE="error" # quiet, error, panic

### DOCKER
CONTAINER_IMAGE="transcribe-demo"

# Check if the Docker image exists
if ! docker image inspect "$CONTAINER_IMAGE" > /dev/null  2>&1; then
  echo "Docker image not found. Building the image..."
  docker build -t "$CONTAINER_IMAGE" .
fi

docker run \
  --env AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
  --env AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
  --env AWS_SESSION_TOKEN="${AWS_SESSION_TOKEN}" \
  --env SOURCE="${SOURCE}" \
  --env LOGLEVEL="${LOGLEVEL}" \
  --env VERBOSE="${VERBOSE}" \
  "$CONTAINER_IMAGE"
