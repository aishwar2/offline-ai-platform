# Troubleshooting Guide

## 1. Slow Responses or Out-of-Memory (OOM) on 4 GB RAM Hosts

- Confirm `OLLAMA_MAX_LOADED_MODELS=1` and `OLLAMA_NUM_PARALLEL=1` are set in `.env` or `kubernetes/configmap.yaml`.
- Switch from `tinyllama` (~637 MB) to `qwen2.5:0.5b` (~398 MB) in **Settings -> Default Model** or the chat header dropdown.
- If host RAM is severely constrained, set `RAG_ENABLED=false` in `.env` to disable ChromaDB initialization.

## 2. Backend `/health/ready` Reports `ollama: unreachable`

- Check Ollama container logs:
  ```bash
  docker logs offline-ai-ollama --tail 100
  ```
- Verify the model is pulled:
  ```bash
  docker exec offline-ai-ollama ollama list
  ```
- Pull manually if offline startup missed it:
  ```bash
  ./scripts/pull-models.sh tinyllama
  ```

## 3. PostgreSQL Connection Errors

- Verify `POSTGRES_PASSWORD` matches in `.env` and `DATABASE_URL`.
- If you changed `POSTGRES_PASSWORD` after initial volume creation, reset the volume (`docker compose down -v`) or alter the role password inside PostgreSQL.

## 4. CORS Errors in Browser

- Add your UI origin (e.g., `http://localhost:5173` or `https://ai.example.com`) to `CORS_ORIGINS` in `.env` and restart the backend container.

## 5. Rate Limit (`429 Too Many Requests`)

- Adjust `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS` in `.env` for higher-concurrency environments.
