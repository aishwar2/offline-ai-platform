#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Health Check Script for Offline AI Platform (Docker Compose or Kubernetes)
# =============================================================================

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3001}"

check_endpoint() {
  local name="$1"
  local url="$2"
  echo -n "Checking ${name} (${url})... "
  if curl -fsS --max-time 5 "$url" >/dev/null; then
    echo "OK"
  else
    echo "FAILED"
    return 1
  fi
}

check_endpoint "Backend Liveness" "${BACKEND_URL}/health/live"
check_endpoint "Backend Readiness" "${BACKEND_URL}/health/ready"
check_endpoint "Backend Metrics" "${BACKEND_URL}/metrics"
check_endpoint "Frontend" "${FRONTEND_URL}/"
check_endpoint "Prometheus" "${PROMETHEUS_URL}/-/healthy"
check_endpoint "Grafana" "${GRAFANA_URL}/api/health"

echo "==> All health checks passed!"
