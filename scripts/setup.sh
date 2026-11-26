#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Offline AI Platform - Initial Setup Script
# Creates .env from .env.example with generated secrets and verifies prerequisites.
# =============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
EXAMPLE_FILE="${ROOT_DIR}/.env.example"

echo "==> Checking prerequisites..."
for cmd in docker; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Error: '$cmd' is required but not installed." >&2
    exit 1
  fi
done

if [ ! -f "$ENV_FILE" ]; then
  echo "==> Creating .env from .env.example..."
  cp "$EXAMPLE_FILE" "$ENV_FILE"

  if command -v openssl >/dev/null 2>&1; then
    JWT_SECRET="$(openssl rand -hex 32)"
    DB_PASS="$(openssl rand -hex 16)"
    GRAFANA_PASS="$(openssl rand -hex 12)"

    sed -i "s|change-this-to-a-long-random-secret-key-min-32-chars|${JWT_SECRET}|g" "$ENV_FILE"
    sed -i "s|change-this-db-password|${DB_PASS}|g" "$ENV_FILE"
    sed -i "s|change-this-grafana-password|${GRAFANA_PASS}|g" "$ENV_FILE"
    echo "==> Generated secure random secrets in .env"
  else
    echo "Warning: openssl not found; please manually update secrets in .env"
  fi
else
  echo "==> .env already exists; skipping creation."
fi

echo "==> Building and starting Offline AI Platform stack..."
docker compose -f "${ROOT_DIR}/docker-compose.yml" up -d --build

echo "==> Pulling lightweight default LLM (tinyllama)..."
"${ROOT_DIR}/scripts/pull-models.sh" tinyllama

echo "==> Setup complete! Services:"
echo "    Frontend UI:   http://localhost:3000"
echo "    Backend API:   http://localhost:8000/docs"
echo "    Prometheus:    http://localhost:9090"
echo "    Grafana:       http://localhost:3001"
