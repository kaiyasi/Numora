#!/usr/bin/env bash
set -euo pipefail

# Start or rebuild+restart Website (web + nginx) via Docker Compose
# If running: rebuild and force-recreate; else: build and start.
# Usage: ./scripts/start_website.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$ROOT_DIR"

# Prefer docker compose if available, fallback to docker-compose
if docker compose version >/dev/null 2>&1; then
  CMD=(docker compose)
else
  CMD=(docker-compose)
fi

SERVICES=(web nginx)
CONTAINERS=(numora-web numora-nginx)

# Check if any target service container is currently running
any_running=false
for cname in "${CONTAINERS[@]}"; do
  if docker ps --filter "name=^/${cname}$" --filter status=running -q >/dev/null 2>&1; then
    if [[ -n "$(docker ps --filter "name=^/${cname}$" --filter status=running -q)" ]]; then
      any_running=true
      break
    fi
  fi
done

if [[ "$any_running" == true ]]; then
  echo "Detected running Website containers. Rebuilding and restarting..."
  "${CMD[@]}" up -d --build --force-recreate "${SERVICES[@]}"
else
  echo "No running Website containers found. Building and starting..."
  "${CMD[@]}" up -d --build "${SERVICES[@]}"
fi

"${CMD[@]}" ps

echo "Website services are up: ${SERVICES[*]}"
