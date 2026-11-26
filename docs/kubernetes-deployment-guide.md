# Kubernetes Deployment Guide

## Prerequisites

- Kubernetes 1.28+ cluster (k3s, kind, minikube, or managed K8s) with at least 2 CPU / 4 GB RAM available.
- `kubectl` configured against your target cluster.
- NGINX Ingress Controller installed (if using `kubernetes/ingress.yaml`).

## Deployment Steps

1. **Update Secrets**

   Edit `kubernetes/secrets.yaml` (or replace with SealedSecrets/ExternalSecrets) so `JWT_SECRET_KEY`, `POSTGRES_PASSWORD`, and `DATABASE_URL` contain strong production credentials.

2. **Build or Push Container Images**

   Ensure `offline-ai-backend:latest`, `offline-ai-frontend:latest`, and `offline-ai-ollama:latest` are available to your cluster nodes (either via Docker Hub or `kind load docker-image` / `k3s ctr images import`).

3. **Apply Manifests with Kustomize**

   ```bash
   kubectl apply -k kubernetes/
   ```

4. **Monitor Rollout**

   ```bash
   kubectl -n offline-ai get pods -w
   kubectl -n offline-ai rollout status deployment/backend
   kubectl -n offline-ai rollout status deployment/frontend
   ```

5. **Access & Verify**

   ```bash
   kubectl -n offline-ai port-forward svc/frontend 3000:80
   kubectl -n offline-ai port-forward svc/backend 8000:8000
   ```
