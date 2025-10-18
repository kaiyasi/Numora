#!/usr/bin/env bash
set -euo pipefail

# Start or rebuild+restart Bot service via Docker Compose
# If running: rebuild and force-recreate; else: build and start.
# Usage: ./scripts/start_bot.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$ROOT_DIR"

# Prefer docker compose if available, fallback to docker-compose
if docker compose version >/dev/null 2>&1; then
  CMD=(docker compose)
else
  CMD=(docker-compose)
fi

SERVICE=bot
CONTAINER=numora-bot

# Determine expected compose project name
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-$(basename "$ROOT_DIR")}"

# Preflight: remove conflicting containers not owned by this compose project
# This prevents "name already in use" errors (e.g., numora-redis)
cleanup_conflict() {
  local cname="$1"
  local cid
  cid=$(docker ps -a --filter "name=^/${cname}$" -q || true)
  [[ -z "$cid" ]] && return 0
  # Identify compose project label on existing container (if any)
  local label
  label=$(docker inspect -f '{{ index .Config.Labels "com.docker.compose.project"}}' "$cname" 2>/dev/null || true)
  if [[ -n "$label" && "$label" == "$PROJECT_NAME" ]]; then
    # Owned by this project; leave it (compose will recreate as needed)
    return 0
  fi
  echo "Found conflicting container '$cname' (project='$label'). Removing..."
  docker rm -f "$cname" >/dev/null 2>&1 || true
}

# Known service container names in this stack
for C in numora-redis numora-db numora-nginx numora-web numora-bot; do
  cleanup_conflict "$C"
done

# Check if the bot container is currently running
if docker ps --filter "name=^/${CONTAINER}$" --filter status=running -q >/dev/null 2>&1 && \
   [[ -n "$(docker ps --filter "name=^/${CONTAINER}$" --filter status=running -q)" ]]; then
  echo "Detected running Bot container. Rebuilding and restarting..."
  "${CMD[@]}" up -d --build --force-recreate --remove-orphans "$SERVICE"
else
  echo "No running Bot container found. Building and starting..."
  "${CMD[@]}" up -d --build --remove-orphans "$SERVICE"
fi

"${CMD[@]}" ps

echo "Bot service is up: $SERVICE"
