#!/bin/bash
set -e
echo "=== Building Docker images ==="
docker build -t llm-logger-backend:latest ./backend
docker build -t llm-logger-frontend:latest ./frontend
echo "=== Deploying to Kubernetes ==="
kubectl apply -f k8s/all.yaml
echo "=== Waiting for pods ==="
kubectl wait --for=condition=ready pod -l app=postgres -n llm-logger --timeout=120s
kubectl wait --for=condition=ready pod -l app=redis -n llm-logger --timeout=60s
kubectl wait --for=condition=ready pod -l app=backend -n llm-logger --timeout=120s
kubectl wait --for=condition=ready pod -l app=frontend -n llm-logger --timeout=60s
echo "=== Done ==="
kubectl get pods -n llm-logger
kubectl get svc -n llm-logger
