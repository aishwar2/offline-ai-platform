#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Pull optimized CPU-friendly models into the Ollama container.
# Usage: ./scripts/pull-models.sh [tinyllama|qwen2.5:0.5b]
# =============================================================================

MODELS=("${@:-tinyllama}")
CONTAINER_NAME="${OLLAMA_CONTAINER:-offline-ai-ollama}"

echo "==> Waiting for Ollama service inside container '${CONTAINER_NAME}'..."
for i in $(seq 1 30); do
  if docker exec "$CONTAINER_NAME" ollama list >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

for model in "${MODELS[@]}"; do
  echo "==> Pulling model: ${model}"
  docker exec "$CONTAINER_NAME" ollama pull "$model"
done

echo "==> Available models:"
docker exec "$CONTAINER_NAME" ollama list
