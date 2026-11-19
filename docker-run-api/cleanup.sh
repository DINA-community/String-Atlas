#!/usr/bin/env bash
set -e
if docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"

# Fallback auf altes "docker-compose"
elif docker-compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
fi

echo "Stopping and removing containers..."
$DOCKER_COMPOSE down

echo "Removing volumes from current compose project..."
$DOCKER_COMPOSE down -v

echo "Removing orphan containers..."
$DOCKER_COMPOSE down --remove-orphans

echo "Cleanup finished."