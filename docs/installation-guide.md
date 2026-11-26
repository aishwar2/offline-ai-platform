# Installation Guide

## Prerequisites

- **Hardware**: Minimum 2 CPU cores, 4 GB RAM, 10 GB free disk space (no GPU required).
- **Software**:
  - Docker Engine 24+ and Docker Compose v2 (`docker compose`)
  - `curl` and `openssl` (used by `scripts/setup.sh`)

## Step-by-Step Installation

1. **Clone the repository**

   ```bash
   git clone <your-repo-url> offline-ai-platform
   cd offline-ai-platform
   ```

2. **Generate environment secrets and launch services**

   ```bash
   chmod +x scripts/*.sh
   ./scripts/setup.sh
   ```

   This script copies `.env.example` to `.env`, generates random credentials for `JWT_SECRET_KEY`, `POSTGRES_PASSWORD`, and `GRAFANA_ADMIN_PASSWORD`, builds all containers, starts the stack, and pulls `tinyllama`.

3. **Optional: Pull Qwen2.5 0.5B for ultra-fast CPU inference**

   ```bash
   ./scripts/pull-models.sh qwen2.5:0.5b
   ```

4. **Verify Stack Health**

   ```bash
   ./scripts/health-check.sh
   ```

5. **Create the First Admin Account**

   Open http://localhost:3000, click **Create Account**, and register your first user. The first registered user is automatically assigned the `admin` role.
