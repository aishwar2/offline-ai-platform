#!/bin/sh
set -eu

# Start Ollama daemon in background, pre-pull default CPU-friendly model if missing, then wait.
ollama serve &
SERVER_PID=$!

DEFAULT_MODEL="${DEFAULT_MODEL:-tinyllama}"

echo "==> Waiting for Ollama server..."
i=0
while [ "$i" -lt 30 ]; do
  if ollama list >/dev/null 2>&1; then
    break
  fi
  i=$((i + 1))
  sleep 1
done

if ! ollama list | grep -q "^${DEFAULT_MODEL}"; then
  echo "==> Pulling default lightweight model: ${DEFAULT_MODEL}"
  ollama pull "${DEFAULT_MODEL}" || echo "Warning: initial pull failed (offline or retrying later)."
fi

wait "$SERVER_PID"
