# 🚀 Complete Deployment Guide - Wellness AI Platform

## 📖 Table of Contents

1. [Quick Start (5 Minutes)](#quick-start-5-minutes)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Production Kubernetes Deployment](#production-kubernetes-deployment)
5. [Building the Project](#building-the-project)
6. [Testing & Verification](#testing--verification)
7. [Troubleshooting](#troubleshooting)
8. [Monitoring & Maintenance](#monitoring--maintenance)

---

## ⚡ Quick Start (5 Minutes)

Get the app running with minimal setup:

### Prerequisites
- Docker & Docker Compose installed
- 8GB RAM minimum
- 10GB free disk space

### Steps

```bash
# 1. Navigate to project directory
cd Wellnessapp

# 2. Copy environment file
cp .env.example .env

# 3. Start all services with Docker Compose
docker-compose up -d

# 4. Wait for services to start (30-60 seconds)
docker-compose ps

# 5. Access the application
```

**Access Points:**
- 🎨 Frontend UI: http://localhost:8501
- 📊 API Docs: http://localhost:8000/docs
- 🔍 GraphQL: http://localhost:8000/graphql
- 📈 MLflow: http://localhost:5000
- 📉 Grafana: http://localhost:3000 (admin/admin)
- 🔬 Prometheus: http://localhost:9090
- 🧠 Neo4j Browser: http://localhost:7474

That's it! The app is now running with all services.

---

## 💻 Local Development Setup

For development without Docker:

### Prerequisites

```bash
# System Requirements
- Python 3.9 or higher
- PostgreSQL 14+
- MongoDB 6+
- Redis 7+
- Neo4j 5+ (optional for GraphRAG)
- 8GB RAM minimum (16GB recommended)
```

### Step 1: Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Setup Databases

#### Option A: Use Docker for databases only

```bash
# Start only database services
docker-compose up -d postgres mongo redis neo4j
```

#### Option B: Install databases locally

**PostgreSQL:**
```bash
# Ubuntu/Debian
sudo apt-get install postgresql-14

# Create database
sudo -u postgres createdb wellness_db
sudo -u postgres createuser wellness_user
sudo -u postgres psql -c "ALTER USER wellness_user WITH PASSWORD 'wellness_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE wellness_db TO wellness_user;"
```

**MongoDB:**
```bash
# Ubuntu/Debian
sudo apt-get install mongodb-org

# Start MongoDB
sudo systemctl start mongod
```

**Redis:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis-server
```

**Neo4j:**
```bash
# Download from neo4j.com/download
# Or use Docker:
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/wellness_password \
  neo4j:5-community
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configurations
nano .env  # or use your preferred editor

# Key configurations to set:
# - Database URLs
# - API keys (OpenAI, Anthropic, etc.)
# - Secret keys
# - Ports
```

### Step 4: Initialize Databases

```bash
# Run database initialization script
python scripts/init_db.py

# Generate sample data (optional)
python scripts/generate_sample_data.py
```

### Step 5: Start Application Services

Open three terminal windows:

**Terminal 1 - Backend API:**
```bash
source venv/bin/activate
cd backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
source venv/bin/activate
streamlit run frontend/app.py --server.port 8501
```

**Terminal 3 - MLflow (Optional):**
```bash
source venv/bin/activate
mlflow ui --port 5000
```

### Alternative: Use Start Script

```bash
# Make script executable
chmod +x start.sh

# Run the master start script
./start.sh
```

The script automatically:
- ✅ Checks database services
- ✅ Initializes databases on first run
- ✅ Starts backend and frontend
- ✅ Shows health status

---

## 🐳 Docker Deployment

### Architecture Overview

Docker Compose spins up 9 services:
1. **PostgreSQL** - Structured data (user profiles, health metrics)
2. **MongoDB** - Unstructured data (journals, raw signals, chat history)
3. **Redis** - Caching and session storage
4. **Neo4j** - Knowledge graph for GraphRAG
5. **Backend** - FastAPI application
6. **Frontend** - Streamlit UI
7. **MLflow** - Experiment tracking
8. **Prometheus** - Metrics collection
9. **Grafana** - Monitoring dashboards

### Full Deployment Steps

#### 1. Prepare Environment

```bash
# Clone repository (if not done)
git clone <your-repo-url>
cd Wellnessapp

# Copy and configure environment
cp .env.example .env

# Edit .env with your settings
# Important: Set these for full functionality
nano .env
```

**Required Environment Variables:**
```env
# LLM Configuration (for AI Coach)
OPENAI_API_KEY=sk-your-openai-key
# OR
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Database Passwords (change defaults!)
POSTGRES_PASSWORD=secure-password-here
MONGODB_PASSWORD=secure-password-here
NEO4J_PASSWORD=secure-password-here

# Security
JWT_SECRET_KEY=generate-random-secret-key
ENCRYPTION_KEY=32-byte-encryption-key-here
```

#### 2. Build and Start Services

```bash
# Build Docker images
docker-compose build

# Start all services in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

#### 3. Verify Services

```bash
# Check all services are healthy
docker-compose ps

# Should show all services as "Up" or "healthy"

# Test backend
curl http://localhost:8000/health

# Test frontend
curl http://localhost:8501
```

#### 4. Initialize Application Data

```bash
# Generate sample data
docker-compose exec backend python /app/scripts/generate_sample_data.py

# Initialize knowledge base
docker-compose exec backend python /app/scripts/init_vector_store.py
```

### Docker Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Stop and remove volumes (CAUTION: Deletes data!)
docker-compose down -v

# View logs
docker-compose logs -f [service-name]

# Restart a service
docker-compose restart [service-name]

# Rebuild a service
docker-compose up -d --build [service-name]

# Execute command in container
docker-compose exec [service-name] [command]

# Scale a service
docker-compose up -d --scale backend=3
```

### Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:8501 | Streamlit web interface |
| Backend API | http://localhost:8000/docs | FastAPI interactive docs |
| GraphQL | http://localhost:8000/graphql | GraphQL playground |
| MLflow | http://localhost:5000 | Experiment tracking |
| Grafana | http://localhost:3000 | Dashboards (admin/admin) |
| Prometheus | http://localhost:9090 | Metrics |
| Neo4j Browser | http://localhost:7474 | Graph database UI |

---

## ☸️ Production Kubernetes Deployment

For production-grade deployment with high availability and scalability.

### Prerequisites

```bash
# Required tools
- kubectl installed and configured
- Kubernetes cluster (GKE, EKS, AKS, or local minikube)
- Docker registry access
- 16GB+ RAM available in cluster
- 50GB+ storage
```

### Step 1: Build and Push Docker Images

```bash
# Set your Docker registry
export DOCKER_REGISTRY=your-registry.azurecr.io
# Or: docker.io/your-username

# Build backend image
docker build -t ${DOCKER_REGISTRY}/wellness-backend:latest \
  -f docker/Dockerfile.backend .

# Build frontend image
docker build -t ${DOCKER_REGISTRY}/wellness-frontend:latest \
  -f docker/Dockerfile.frontend .

# Push images to registry
docker push ${DOCKER_REGISTRY}/wellness-backend:latest
docker push ${DOCKER_REGISTRY}/wellness-frontend:latest
```

### Step 2: Configure Kubernetes Manifests

```bash
# Update image references in deployments
cd k8s

# Update backend-deployment.yaml
sed -i "s|wellness-ai/backend:latest|${DOCKER_REGISTRY}/wellness-backend:latest|g" backend-deployment.yaml

# Update frontend-deployment.yaml
sed -i "s|wellness-ai/frontend:latest|${DOCKER_REGISTRY}/wellness-frontend:latest|g" frontend-deployment.yaml
```

### Step 3: Create Kubernetes Secrets

```bash
# Create namespace
kubectl create namespace wellness-ai

# Create secrets from environment file
kubectl create secret generic wellness-secrets \
  --from-literal=postgres-password=your-secure-password \
  --from-literal=mongodb-password=your-secure-password \
  --from-literal=neo4j-password=your-secure-password \
  --from-literal=openai-api-key=sk-your-key \
  --from-literal=jwt-secret=your-jwt-secret \
  -n wellness-ai

# Or use the secrets.yaml file (after base64 encoding values)
# Base64 encode secrets:
echo -n 'your-password' | base64

# Update k8s/secrets.yaml with encoded values
kubectl apply -f secrets.yaml
```

### Step 4: Deploy to Kubernetes

```bash
# Apply all Kubernetes manifests in order
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml

# Deploy databases
kubectl apply -f postgres-deployment.yaml
kubectl apply -f mongodb-deployment.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f neo4j-deployment.yaml

# Wait for databases to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n wellness-ai --timeout=300s

# Deploy application services
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml

# Deploy monitoring
kubectl apply -f prometheus-deployment.yaml
kubectl apply -f grafana-deployment.yaml
kubectl apply -f mlflow-deployment.yaml

# Deploy autoscaling
kubectl apply -f hpa.yaml
```

### Step 5: Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n wellness-ai

# Check services
kubectl get svc -n wellness-ai

# View logs
kubectl logs -f deployment/wellness-backend -n wellness-ai

# Check pod health
kubectl describe pod <pod-name> -n wellness-ai
```

### Step 6: Access the Application

```bash
# Get external IPs (if using LoadBalancer)
kubectl get svc -n wellness-ai

# Or use port forwarding for testing
kubectl port-forward svc/wellness-frontend 8501:8501 -n wellness-ai
kubectl port-forward svc/wellness-backend 8000:8000 -n wellness-ai
```

### Step 7: Setup Ingress (Optional)

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml

# Create Ingress resource
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: wellness-ingress
  namespace: wellness-ai
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - wellness-ai.yourdomain.com
    - api.wellness-ai.yourdomain.com
    secretName: wellness-tls
  rules:
  - host: wellness-ai.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: wellness-frontend
            port:
              number: 8501
  - host: api.wellness-ai.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: wellness-backend
            port:
              number: 8000
EOF
```

### Kubernetes Monitoring

```bash
# Watch resource usage
kubectl top nodes
kubectl top pods -n wellness-ai

# View HPA status
kubectl get hpa -n wellness-ai

# Check events
kubectl get events -n wellness-ai --sort-by='.lastTimestamp'
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment wellness-backend --replicas=5 -n wellness-ai

# Autoscaling is configured via HPA (already applied)
# Scales based on CPU/Memory utilization
```

---

## 🔨 Building the Project

### Building from Source

```bash
# Full build process
cd Wellnessapp

# 1. Install dependencies
pip install -r requirements.txt

# 2. Run tests
pytest tests/ -v --cov=backend --cov=ml

# 3. Build documentation (if using MkDocs)
mkdocs build

# 4. Train models (optional)
python ml/training/train_eeg_model.py
```

### Building Docker Images

```bash
# Backend
docker build \
  -t wellness-backend:latest \
  -f docker/Dockerfile.backend \
  --build-arg PYTHON_VERSION=3.9 \
  .

# Frontend
docker build \
  -t wellness-frontend:latest \
  -f docker/Dockerfile.frontend \
  .

# Tag for registry
docker tag wellness-backend:latest ${DOCKER_REGISTRY}/wellness-backend:v1.0.0
docker tag wellness-frontend:latest ${DOCKER_REGISTRY}/wellness-frontend:v1.0.0

# Push to registry
docker push ${DOCKER_REGISTRY}/wellness-backend:v1.0.0
docker push ${DOCKER_REGISTRY}/wellness-frontend:v1.0.0
```

### CI/CD Pipeline (GitHub Actions Example)

Create `.github/workflows/deploy.yml`:

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run tests
        run: |
          pytest tests/ -v

      - name: Build Docker images
        run: |
          docker build -t ${{ secrets.DOCKER_REGISTRY }}/wellness-backend:${{ github.sha }} -f docker/Dockerfile.backend .
          docker build -t ${{ secrets.DOCKER_REGISTRY }}/wellness-frontend:${{ github.sha }} -f docker/Dockerfile.frontend .

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push ${{ secrets.DOCKER_REGISTRY }}/wellness-backend:${{ github.sha }}
          docker push ${{ secrets.DOCKER_REGISTRY }}/wellness-frontend:${{ github.sha }}

      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/wellness-backend wellness-backend=${{ secrets.DOCKER_REGISTRY }}/wellness-backend:${{ github.sha }} -n wellness-ai
          kubectl set image deployment/wellness-frontend wellness-frontend=${{ secrets.DOCKER_REGISTRY }}/wellness-frontend:${{ github.sha }} -n wellness-ai
```

---

## ✅ Testing & Verification

### Automated Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=backend --cov=ml --cov-report=html

# Run specific test files
pytest tests/test_eeg_analysis.py -v
pytest tests/test_api_endpoints.py -v
pytest tests/test_coach_service.py -v

# Run only unit tests
pytest tests/ -v -m unit

# Run only integration tests
pytest tests/ -v -m integration
```

### Manual API Testing

```bash
# Health check
curl http://localhost:8000/health

# Upload EEG data
curl -X POST "http://localhost:8000/api/v1/eeg/upload" \
  -H "accept: application/json" \
  -F "file=@data/sample_data/sample_eeg.csv"

# Chat with AI coach
curl -X POST "http://localhost:8000/api/v1/coach/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I feel stressed and have trouble sleeping",
    "user_id": "test_user",
    "include_context": true
  }'

# Voice emotion analysis
curl -X POST "http://localhost:8000/api/v1/voice/analyze" \
  -F "file=@path/to/audio.wav"

# Food recognition
curl -X POST "http://localhost:8000/api/v1/food/recognize" \
  -F "file=@path/to/food_image.jpg"

# Get recommendations
curl "http://localhost:8000/api/v1/recommendations/generate?user_id=test_user"
```

### GraphQL Testing

Visit http://localhost:8000/graphql and try:

```graphql
# Query health metrics
query {
  healthMetrics(userId: "test_user") {
    id
    date
    steps
    sleepHours
    stressLevel
    mood
  }
}

# Log new health data
mutation {
  logHealthMetrics(
    userId: "test_user"
    date: "2024-01-15"
    steps: 8500
    sleepHours: 7.5
    stressLevel: 3
    mood: "good"
  ) {
    id
    success
    message
  }
}

# Get user profile
query {
  user(userId: "test_user") {
    id
    name
    email
    doshaProfile {
      vata
      pitta
      kapha
    }
  }
}
```

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test API endpoint
ab -n 1000 -c 10 http://localhost:8000/health

# Install Locust for advanced testing
pip install locust

# Create locustfile.py and run
locust -f tests/load_test.py --host=http://localhost:8000
```

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. Database Connection Errors

```bash
# Check if databases are running
docker-compose ps

# View database logs
docker-compose logs postgres
docker-compose logs mongo

# Restart databases
docker-compose restart postgres mongo redis neo4j

# Verify connectivity
docker-compose exec backend python -c "
from backend.database.postgres_db import test_connection
test_connection()
"
```

#### 2. Port Already in Use

```bash
# Find process using port
sudo lsof -i :8000
sudo lsof -i :8501

# Kill process
kill -9 <PID>

# Or change ports in .env
BACKEND_PORT=8001
FRONTEND_PORT=8502
```

#### 3. Out of Memory

```bash
# Check Docker memory
docker stats

# Increase Docker Desktop memory limit (Mac/Windows)
# Docker Desktop -> Settings -> Resources -> Memory

# Reduce services for limited RAM
docker-compose up -d postgres mongo redis backend frontend
```

#### 4. Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Verify Python path
python -c "import sys; print(sys.path)"

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/Wellnessapp"
```

#### 5. Model Not Found Errors

```bash
# Download pre-trained models
python scripts/download_models.py

# Or use smaller models
# Edit config/settings.py:
USE_LOCAL_LLM = False  # Use API instead of local model
```

#### 6. ChromaDB/Vector Database Issues

```bash
# Reset vector database
python -c "
from backend.services.vector_db import get_vector_db
vdb = get_vector_db()
vdb.reset_database()
vdb.load_knowledge_base()
print('Vector DB reset complete')
"
```

#### 7. Neo4j Connection Issues

```bash
# Check Neo4j logs
docker-compose logs neo4j

# Access Neo4j browser
open http://localhost:7474
# Username: neo4j
# Password: (from .env NEO4J_PASSWORD)

# Test connection
python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'your-password'))
with driver.session() as session:
    result = session.run('RETURN 1 as test')
    print(result.single()['test'])
driver.close()
"
```

#### 8. Frontend Not Loading

```bash
# Check backend is running
curl http://localhost:8000/health

# View frontend logs
docker-compose logs frontend

# Restart frontend
docker-compose restart frontend

# Check Streamlit configuration
streamlit config show
```

### Debugging Commands

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend

# Enter container shell
docker-compose exec backend bash

# Check environment variables
docker-compose exec backend env

# Test database migrations
docker-compose exec backend python -m backend.database.migrations

# Run Python REPL in container
docker-compose exec backend python
```

---

## 📊 Monitoring & Maintenance

### Prometheus Metrics

Access: http://localhost:9090

**Key Metrics to Monitor:**
```promql
# API request rate
rate(http_requests_total[5m])

# API latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# EEG processing time
rate(eeg_analysis_duration_seconds[5m])

# Database connection pool
postgres_connections_active
mongodb_connections_current

# Memory usage
process_resident_memory_bytes

# Error rate
rate(http_requests_total{status=~"5.."}[5m])
```

### Grafana Dashboards

Access: http://localhost:3000 (admin/admin)

**Pre-configured Dashboards:**
1. **API Performance** - Request rates, latency, error rates
2. **ML Model Metrics** - Inference times, model accuracy
3. **User Health KPIs** - Aggregated wellness metrics
4. **System Resources** - CPU, memory, disk usage
5. **Database Performance** - Query times, connections

### MLflow Tracking

Access: http://localhost:5000

**Features:**
- Experiment tracking for model training
- Model versioning and registry
- Parameter comparison
- Artifact storage

```bash
# Log experiment
python -c "
import mlflow
mlflow.set_tracking_uri('http://localhost:5000')
mlflow.set_experiment('wellness-eeg')

with mlflow.start_run():
    mlflow.log_param('learning_rate', 0.001)
    mlflow.log_metric('accuracy', 0.95)
    mlflow.log_artifact('model.pth')
"
```

### Backup Strategy

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U wellness_user wellness_db > backup_postgres_$(date +%Y%m%d).sql

# Backup MongoDB
docker-compose exec mongo mongodump --out=/backup --db=wellness_mongo
docker cp wellness-mongo:/backup ./backup_mongo_$(date +%Y%m%d)

# Backup volumes
docker run --rm \
  -v wellness_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz /data

# Restore PostgreSQL
docker-compose exec -T postgres psql -U wellness_user wellness_db < backup_postgres_20240115.sql
```

### Log Management

```bash
# Configure log rotation in docker-compose.yml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

# View aggregated logs
docker-compose logs --tail=100 -f

# Export logs
docker-compose logs > application_logs_$(date +%Y%m%d).log
```

### Health Checks

```bash
# Create health check script
cat > scripts/health_check.sh << 'EOF'
#!/bin/bash

echo "=== Wellness AI Health Check ==="

# Backend
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ Backend: OK"
else
    echo "❌ Backend: FAILED"
fi

# Frontend
if curl -s http://localhost:8501 > /dev/null; then
    echo "✅ Frontend: OK"
else
    echo "❌ Frontend: FAILED"
fi

# PostgreSQL
if docker-compose exec -T postgres pg_isready -U wellness_user > /dev/null; then
    echo "✅ PostgreSQL: OK"
else
    echo "❌ PostgreSQL: FAILED"
fi

# MongoDB
if docker-compose exec -T mongo mongosh --eval "db.adminCommand('ping')" > /dev/null; then
    echo "✅ MongoDB: OK"
else
    echo "❌ MongoDB: FAILED"
fi

# Redis
if docker-compose exec -T redis redis-cli ping > /dev/null; then
    echo "✅ Redis: OK"
else
    echo "❌ Redis: FAILED"
fi

echo "=== End Health Check ==="
EOF

chmod +x scripts/health_check.sh

# Run health check
./scripts/health_check.sh
```

### Performance Optimization

```bash
# Enable caching
# Update .env:
ENABLE_REDIS_CACHE=True
CACHE_TTL=3600

# Optimize database queries
# Add indexes in PostgreSQL
docker-compose exec postgres psql -U wellness_user wellness_db -c "
CREATE INDEX idx_health_metrics_user_date ON health_metrics(user_id, date);
CREATE INDEX idx_eeg_results_user ON eeg_results(user_id);
"

# Configure connection pooling
# In config/settings.py:
POSTGRES_POOL_SIZE=20
POSTGRES_MAX_OVERFLOW=10
```

---

## 🔐 Security Best Practices

### Production Checklist

- [ ] Change all default passwords
- [ ] Generate strong JWT secret keys
- [ ] Enable HTTPS (use Let's Encrypt)
- [ ] Configure firewall rules
- [ ] Enable database encryption at rest
- [ ] Set up VPN for database access
- [ ] Implement rate limiting
- [ ] Enable CORS restrictions
- [ ] Set up log monitoring and alerts
- [ ] Regular security updates
- [ ] Backup encryption
- [ ] Secrets management (use Vault or cloud KMS)

### Environment Security

```bash
# Never commit .env file
echo ".env" >> .gitignore

# Use secrets management in Kubernetes
kubectl create secret generic wellness-secrets \
  --from-env-file=.env \
  -n wellness-ai

# Rotate secrets regularly
# Create script: scripts/rotate_secrets.sh
```

---

## 📚 Additional Resources

### Documentation Files
- `README.md` - Project overview and architecture
- `DEPLOYMENT_GUIDE.md` - Detailed deployment instructions
- `QUICKSTART.md` - Fast onboarding guide
- `docs/API_DOCUMENTATION.md` - Complete API reference
- `docs/USER_GUIDE.md` - End-user documentation
- `k8s/README.md` - Kubernetes deployment guide

### Useful Commands Cheat Sheet

```bash
# Docker Compose
docker-compose up -d              # Start all services
docker-compose down               # Stop all services
docker-compose ps                 # List services
docker-compose logs -f            # View logs
docker-compose restart [service]  # Restart service

# Kubernetes
kubectl get pods -n wellness-ai                    # List pods
kubectl logs -f deployment/wellness-backend        # View logs
kubectl describe pod <pod-name> -n wellness-ai     # Pod details
kubectl exec -it <pod-name> -n wellness-ai -- bash # Shell access
kubectl scale deployment wellness-backend --replicas=3  # Scale

# Application
./start.sh                        # Start application
./scripts/stop_services.sh        # Stop services
pytest tests/ -v                  # Run tests
python scripts/generate_sample_data.py  # Generate data

# Database
docker-compose exec postgres psql -U wellness_user wellness_db
docker-compose exec mongo mongosh wellness_mongo
docker-compose exec redis redis-cli
```

---

## 🆘 Getting Help

- **Documentation**: See links above
- **API Docs**: http://localhost:8000/docs
- **Issues**: GitHub Issues
- **Logs**: `docker-compose logs -f`

---

## 📝 Changelog

### v1.0.0 - Initial Release

**Features:**
- ✅ EEG brain signal analysis
- ✅ AI wellness coach with RAG
- ✅ GraphRAG knowledge graph
- ✅ Voice emotion detection
- ✅ Food recognition
- ✅ Supplement OCR
- ✅ Personalized recommendations
- ✅ Multi-page Streamlit UI
- ✅ Docker Compose deployment
- ✅ Kubernetes manifests
- ✅ Complete test suite

**Tech Stack:**
- Backend: FastAPI + GraphQL
- Databases: PostgreSQL, MongoDB, Redis, Neo4j
- AI/ML: PyTorch, LangChain, ChromaDB
- Frontend: Streamlit
- DevOps: Docker, Kubernetes, MLflow, Prometheus, Grafana

---

**Built with ❤️ for holistic wellness through AI**

**Disclaimer**: This is a research and educational project. Always consult qualified healthcare professionals for medical advice.
