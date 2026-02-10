#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "==> Stopping running containers..."
docker compose down

echo "==> Pulling latest changes..."
git pull origin master

echo "==> Building Docker image (version: $(git rev-parse --short HEAD))..."
APP_VERSION=$(git rev-parse --short HEAD) docker compose build

echo "==> Starting containers..."
APP_VERSION=$(git rev-parse --short HEAD) docker compose up -d

echo "==> Done. Dashboard running at http://localhost:5000"
docker compose ps
