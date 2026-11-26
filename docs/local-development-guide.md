# Local Development Guide

## Running Backend Locally (Python 3.12)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Uses SQLite by default if DATABASE_URL is not overridden
export JWT_SECRET_KEY="local-dev-secret-key-at-least-32-characters"
export OLLAMA_BASE_URL="http://localhost:11434"
uvicorn app.main:app --reload --port 8000
```

Run backend linter and unit tests:

```bash
cd backend
ruff check app tests
pytest -v
```

## Running Frontend Locally (Node.js 22+)

```bash
cd frontend
npm install
npm run dev
```

Vite serves the UI at http://localhost:5173 and proxies `/api`, `/health`, and `/metrics` to `http://localhost:8000`.

Run frontend lint, typecheck, and unit tests:

```bash
cd frontend
npm run lint
npx tsc --noEmit
npm test
```
