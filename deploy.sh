#!/bin/bash

set -e

REMOTE_USER="kivaschenko"
REMOTE_HOST="65.108.68.57"
REMOTE_PATH="/home/kivaschenko/project"

COMMIT_HASH=$(git rev-parse --short HEAD)

echo "🔍 Checking changed folders since last commit..."

# BACKEND_CHANGED=$(git diff --name-only HEAD~1 HEAD | grep '^backend/' || true)
# FRONTEND_CHANGED=$(git diff --name-only HEAD~1 HEAD | grep '^frontend/' || true)
# NOTIFY_CHANGED=$(git diff --name-only HEAD~1 HEAD | grep '^notifications/' || true)

# Manually set changed folders for testing
BACKEND_CHANGED=true
FRONTEND_CHANGED=true
NOTIFY_CHANGED=true
# Uncomment the above lines to simulate changes in all folders for testing

if [[ -n "$BACKEND_CHANGED" ]]; then
    echo "📦 Building backend image..."
    docker build -t backend:ci backend
    docker save backend:ci | gzip > backend.tar.gz
fi

if [[ -n "$FRONTEND_CHANGED" ]]; then
    echo "📦 Building frontend image..."
    docker build -t frontend:ci frontend
    docker save frontend:ci | gzip > frontend.tar.gz
fi

if [[ -n "$NOTIFY_CHANGED" ]]; then
    echo "📦 Building notifications image..."
    docker build -t notifications:ci notifications
    docker save notifications:ci | gzip > notifications.tar.gz
fi

echo "📤 Uploading images to remote server..."

[[ -f backend.tar.gz ]] && scp backend.tar.gz "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
[[ -f frontend.tar.gz ]] && scp frontend.tar.gz "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
[[ -f notifications.tar.gz ]] && scp notifications.tar.gz "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"

echo "🚀 Deploying on remote server..."

ssh "$REMOTE_USER@$REMOTE_HOST" <<EOF
  cd "$REMOTE_PATH"
  [ -f backend.tar.gz ] && gunzip -c backend.tar.gz | docker load && rm backend.tar.gz
  [ -f frontend.tar.gz ] && gunzip -c frontend.tar.gz | docker load && rm frontend.tar.gz
  [ -f notifications.tar.gz ] && gunzip -c notifications.tar.gz | docker load && rm notifications.tar.gz
  docker-compose up -d
EOF

rm -f backend.tar.gz frontend.tar.gz notifications.tar.gz

echo "✅ Deploy complete for commit: $COMMIT_HASH"
