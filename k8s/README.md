# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying the Wellness AI platform.

## Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Helm (optional, for easier management)
- NGINX Ingress Controller
- Cert-Manager (for SSL/TLS)

## Deployment Steps

### 1. Create Namespace

```bash
kubectl apply -f namespace.yaml
```

### 2. Create ConfigMap and Secrets

**IMPORTANT**: Update `secrets.yaml` with actual base64-encoded secrets before deploying!

```bash
# Update secrets first!
# Generate base64: echo -n 'your-secret' | base64

kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
```

### 3. Deploy Databases

```bash
kubectl apply -f postgres-deployment.yaml
kubectl apply -f mongodb-deployment.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f neo4j-deployment.yaml
```

Wait for databases to be ready:

```bash
kubectl wait --for=condition=ready pod -l app=postgres -n wellness-ai --timeout=300s
kubectl wait --for=condition=ready pod -l app=mongodb -n wellness-ai --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n wellness-ai --timeout=300s
kubectl wait --for=condition=ready pod -l app=neo4j -n wellness-ai --timeout=300s
```

### 4. Deploy Application

```bash
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
```

### 5. Deploy MLOps & Monitoring

```bash
kubectl apply -f mlflow-deployment.yaml
kubectl apply -f prometheus-deployment.yaml
kubectl apply -f grafana-deployment.yaml
```

### 6. Configure Autoscaling

```bash
kubectl apply -f hpa.yaml
```

## Verify Deployment

```bash
# Check all pods
kubectl get pods -n wellness-ai

# Check services
kubectl get svc -n wellness-ai

# Check ingresses
kubectl get ingress -n wellness-ai

# View logs
kubectl logs -f deployment/backend -n wellness-ai
kubectl logs -f deployment/frontend -n wellness-ai
```

## Access Services

### Backend API
- Internal: `http://backend.wellness-ai.svc.cluster.local:8000`
- External: `https://api.wellness-ai.example.com`
- API Docs: `https://api.wellness-ai.example.com/docs`

### Frontend
- External: `https://wellness-ai.example.com`

### MLflow
- Internal: `http://mlflow.wellness-ai.svc.cluster.local:5000`

### Grafana
- External: `http://<EXTERNAL-IP>:3000`
- Default login: admin/admin

### Prometheus
- Internal: `http://prometheus.wellness-ai.svc.cluster.local:9090`

## Scaling

### Manual Scaling

```bash
# Scale backend
kubectl scale deployment backend --replicas=5 -n wellness-ai

# Scale frontend
kubectl scale deployment frontend --replicas=3 -n wellness-ai
```

### Autoscaling

HPA is configured to automatically scale based on CPU/memory usage.

View autoscaling status:

```bash
kubectl get hpa -n wellness-ai
```

## Update Deployment

### Rolling Update

```bash
# Update backend image
kubectl set image deployment/backend backend=wellness-ai-backend:v2.0 -n wellness-ai

# Check rollout status
kubectl rollout status deployment/backend -n wellness-ai

# Rollback if needed
kubectl rollout undo deployment/backend -n wellness-ai
```

## Maintenance

### Backup Databases

```bash
# Postgres backup
kubectl exec -it deployment/postgres -n wellness-ai -- pg_dump -U postgres wellness_db > backup.sql

# MongoDB backup
kubectl exec -it deployment/mongodb -n wellness-ai -- mongodump --out=/backup

# Neo4j backup
kubectl exec -it deployment/neo4j -n wellness-ai -- neo4j-admin dump --database=neo4j --to=/backup/neo4j.dump
```

### View Resource Usage

```bash
# Pod resource usage
kubectl top pods -n wellness-ai

# Node resource usage
kubectl top nodes
```

## Troubleshooting

### Pod not starting

```bash
# Describe pod
kubectl describe pod <pod-name> -n wellness-ai

# View events
kubectl get events -n wellness-ai --sort-by='.lastTimestamp'
```

### Database connection issues

```bash
# Test database connectivity
kubectl run -it --rm debug --image=postgres:14-alpine --restart=Never -n wellness-ai -- psql -h postgres -U postgres -d wellness_db
```

### View application logs

```bash
# Backend logs
kubectl logs -f deployment/backend -n wellness-ai

# Frontend logs
kubectl logs -f deployment/frontend -n wellness-ai

# All pods
kubectl logs -f -l app=backend -n wellness-ai --all-containers=true
```

## Security Considerations

1. **Update Secrets**: Replace all placeholder secrets in `secrets.yaml`
2. **TLS/SSL**: Configure cert-manager for automatic SSL certificate management
3. **Network Policies**: Implement network policies to restrict pod-to-pod communication
4. **RBAC**: Set up proper Role-Based Access Control
5. **Pod Security**: Use Pod Security Policies or Pod Security Standards
6. **Image Security**: Use private container registry and scan images for vulnerabilities

## Production Checklist

- [ ] Update all secrets with strong, unique values
- [ ] Configure SSL/TLS certificates
- [ ] Set up proper DNS records
- [ ] Configure resource limits and requests
- [ ] Enable monitoring and alerting
- [ ] Set up log aggregation (ELK stack, Loki, etc.)
- [ ] Configure backups for databases
- [ ] Implement network policies
- [ ] Set up RBAC
- [ ] Configure pod security policies
- [ ] Use private container registry
- [ ] Enable audit logging
- [ ] Set up disaster recovery plan
- [ ] Configure rate limiting on Ingress
- [ ] Enable WAF (Web Application Firewall)

## Clean Up

To remove all resources:

```bash
kubectl delete namespace wellness-ai
```

Or delete individual components:

```bash
kubectl delete -f .
```
