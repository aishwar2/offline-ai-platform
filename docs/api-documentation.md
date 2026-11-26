# API Documentation

Interactive OpenAPI / Swagger documentation is served automatically at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Endpoint Summary (`/api/v1`)

| Group | Method & Path | Description |
| --- | --- | --- |
| **Health** | `GET /health/live` | Liveness probe |
| **Health** | `GET /health/ready` | Readiness probe (DB + Ollama status) |
| **Metrics** | `GET /metrics` | Prometheus metrics endpoint |
| **Auth** | `POST /api/v1/auth/register` | Register account (first user becomes `admin`) |
| **Auth** | `POST /api/v1/auth/login` | Obtain HS256 JWT access token |
| **Users** | `GET /api/v1/users/me` | Fetch authenticated user profile |
| **Users** | `PATCH /api/v1/users/me` | Update full name, default model, or password |
| **Users (Admin)** | `GET /api/v1/users` | List all users |
| **Users (Admin)** | `PATCH /api/v1/users/{id}` | Update user role or active flag |
| **Users (Admin)** | `DELETE /api/v1/users/{id}` | Delete user account |
| **Conversations** | `GET /api/v1/conversations` | List user's conversations |
| **Conversations** | `POST /api/v1/conversations` | Create conversation |
| **Conversations** | `GET /api/v1/conversations/{id}` | Get conversation with messages |
| **Conversations** | `PATCH /api/v1/conversations/{id}` | Rename, switch model, or toggle RAG |
| **Conversations** | `DELETE /api/v1/conversations/{id}` | Delete conversation |
| **Conversations** | `GET /api/v1/conversations/{id}/export?format=markdown\|json` | Export chat history |
| **Chat & AI** | `GET /api/v1/chat/models` | List locally installed Ollama models |
| **Chat & AI** | `POST /api/v1/chat` | Stream SSE tokens or return JSON completion |
| **RAG / Agents / MCP** | `POST /api/v1/rag/documents` | Upload PDF/TXT/MD for ChromaDB indexing |
| **RAG / Agents / MCP** | `GET /api/v1/rag/documents` | List uploaded documents |
| **RAG / Agents / MCP** | `DELETE /api/v1/rag/documents/{id}` | Remove document and chunks |
| **RAG / Agents / MCP** | `POST /api/v1/rag/query` | Query relevant document chunks |
| **RAG / Agents / MCP** | `POST /api/v1/rag/agent` | Execute Plan-Retrieve-Synthesize agent task |
| **RAG / Agents / MCP** | `POST /api/v1/rag/mcp` | JSON-RPC 2.0 MCP server endpoint |
