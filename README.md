# Offline AI Platform

A production-ready, fully offline ChatGPT-style AI platform engineered to run on modest hardware (**2 vCPU, 4 GB RAM, No GPU**) using **TinyLlama** (`tinyllama`) or **Qwen2.5 0.5B** (`qwen2.5:0.5b`) via **Ollama**.

## Key Capabilities

- **Authentication & RBAC**: JWT authentication, user registration/login, profile preferences, and admin user management.
- **Modern ChatGPT-Style UI**: React + TypeScript + TailwindCSS SPA with dark mode, responsive sidebar, conversation history, model switcher, streaming SSE output, token/latency badges, and Markdown/JSON export.
- **Local AI Inference**: Connects directly to Ollama (`/api/chat`, `/api/tags`) with TinyLlama as default, token counting, and response-time tracking.
- **Database Persistence**: PostgreSQL 16 + SQLAlchemy 2.0 ORM (`users`, `conversations`, `messages`, `documents`).
- **Optional Advanced Features**: PDF/Text upload & RAG with ChromaDB, lightweight multi-step Agent workflows (`/api/v1/rag/agent`), and a built-in Model Context Protocol (MCP) JSON-RPC 2.0 server (`/api/v1/rag/mcp`).
- **Observability**: Prometheus (`/metrics`), Node Exporter, and pre-provisioned Grafana dashboards covering CPU, Memory, Requests/sec, API latency, Token count, and Model response times.
- **Security & DevOps**: Non-root Docker images, rate limiting, structured JSON logging, Kubernetes manifests (`kustomize`), and a 5-stage GitHub Actions CI/CD pipeline.

## Repository Structure

```text
offline-ai-platform/
├── backend/                  # FastAPI API, SQLAlchemy ORM, Ollama/RAG/MCP services, pytest suite
├── frontend/                 # React + TypeScript + TailwindCSS SPA + Nginx config
├── ollama/                   # Non-root Ollama container & model pre-pull entrypoint
├── database/                 # PostgreSQL schema & development seed SQL
├── monitoring/               # Prometheus scrape config & Grafana provisioned dashboards
├── kubernetes/               # Namespace, ConfigMap, Secrets, Deployments, Services, Ingress
├── docs/                     # Installation, Local Dev, K8s, Troubleshooting, and API guides
├── scripts/                  # Setup, model pull, and health-check helper scripts
├── .github/workflows/        # 5-stage GitHub Actions CI/CD workflow
├── docker-compose.yml        # Full-stack Compose definition optimized for 2 CPU / 4 GB RAM
├── architecture.md           # System architecture diagram & resource budget breakdown
└── .env.example              # Environment configuration template
```

## Quick Start (Docker Compose)

```bash
git clone <your-repo-url> offline-ai-platform
cd offline-ai-platform
chmod +x scripts/*.sh
./scripts/setup.sh
```

Once running, access:
- **Chat UI**: http://localhost:3000
- **Swagger API Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (credentials from `.env`)

Pull an optional ultra-light alternative model (`qwen2.5:0.5b`):

```bash
./scripts/pull-models.sh qwen2.5:0.5b
```

## Documentation Index

- [Architecture & Resource Budget](architecture.md)
- [Installation Guide](docs/installation-guide.md)
- [Local Development Guide](docs/local-development-guide.md)
- [Kubernetes Deployment Guide](docs/kubernetes-deployment-guide.md)
- [API Documentation](docs/api-documentation.md)
- [Troubleshooting Guide](docs/troubleshooting-guide.md)
