# Wellness AI - Deployment Guide

**Version:** 1.0.0
**Platform:** Docker + Kubernetes (Production) / Docker Compose (Development)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Environment Configuration](#environment-configuration)
4. [Database Setup](#database-setup)
5. [Docker Deployment](#docker-deployment)
6. [Kubernetes Deployment](#kubernetes-deployment)
7. [Cloud Deployment Options](#cloud-deployment-options)
8. [SSL/TLS Configuration](#ssltls-configuration)
9. [Monitoring & Logging](#monitoring--logging)
10. [Backup & Recovery](#backup--recovery)
11. [Scaling](#scaling)
12. [CI/CD Pipeline](#cicd-pipeline)
13. [Security Hardening](#security-hardening)
14. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Development:**
- OS: Linux, macOS, or Windows 10/11
- RAM: 8GB minimum, 16GB recommended
- Storage: 20GB free space
- CPU: 4 cores minimum

**Production:**
- RAM: 16GB minimum, 32GB recommended
- Storage: 100GB+ (depends on user data)
- CPU: 8+ cores
- Network: 100 Mbps+ bandwidth

### Software Requirements

**Required:**
- Docker 20.10+ ([Install](https://docs.docker.com/get-docker/))
- Docker Compose 2.0+ ([Install](https://docs.docker.com/compose/install/))
- Git ([Install](https://git-scm.com/downloads))

**Optional (for Kubernetes deployment):**
- kubectl ([Install](https://kubernetes.io/docs/tasks/tools/))
- Helm 3+ ([Install](https://helm.sh/docs/intro/install/))
- Kubernetes cluster (local: Minikube, k3s, or cloud: AWS EKS, GCP GKE, Azure AKS)

**Development Tools:**
- Python 3.10+
- Node.js 18+ (for any future frontend builds)
- PostgreSQL client (for database management)
- Redis client (optional)

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/Wellnessapp.git
cd Wellnessapp
```

### 2. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` with your settings (see [Environment Configuration](#environment-configuration)).

### 3. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Start Development Services with Docker Compose

```bash
docker-compose up -d postgres mongo redis neo4j
```

Wait 30 seconds for databases to initialize.

### 5. Initialize Databases

```bash
# Run database migrations
python backend/database/init_db.py
```

### 6. Start Backend Server

```bash
# Option 1: Direct Python
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Option 2: Docker
docker-compose up -d backend
```

Backend will be available at: `http://localhost:8000`

### 7. Start Frontend

```bash
# Option 1: Direct Python
cd frontend
streamlit run app.py --server.port 8501

# Option 2: Docker
docker-compose up -d frontend
```

Frontend will be available at: `http://localhost:8501`

### 8. Verify Installation

Open browser and navigate to:
- Frontend: http://localhost:8501
- API Docs: http://localhost:8000/docs
- API Health: http://localhost:8000/health

**Test Login:**
- Email: `demo@wellnessai.com`
- Password: `demo123`

---

## Environment Configuration

### .env File Structure

Create `.env` in project root:

```bash
# ============================================================================
# APPLICATION
# ============================================================================
APP_NAME=Wellness AI
DEBUG=false
ENV=production
SECRET_KEY=<generate-with: openssl rand -hex 32>

# ============================================================================
# JWT AUTHENTICATION
# ============================================================================
JWT_SECRET_KEY=<generate-with: openssl rand -hex 32>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS=30

# ============================================================================
# DATABASES
# ============================================================================

# PostgreSQL (Structured Data)
DATABASE_URL=postgresql://wellness_user:secure_password@postgres:5432/wellness_db

# MongoDB (Unstructured Data)
MONGODB_URL=mongodb://wellness_user:secure_password@mongo:27017/wellness_db

# Redis (Caching)
REDIS_URL=redis://redis:6379/0

# Neo4j (Knowledge Graph)
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=secure_password

# ============================================================================
# LLM & AI SERVICES
# ============================================================================

# OpenAI (for GPT models)
OPENAI_API_KEY=sk-...  # Get from https://platform.openai.com/api-keys

# Anthropic (for Claude models)
ANTHROPIC_API_KEY=sk-ant-...  # Get from https://console.anthropic.com/

# HuggingFace (for open-source models)
HUGGINGFACE_API_KEY=hf_...  # Get from https://huggingface.co/settings/tokens

# Pinecone (Vector Database)
PINECONE_API_KEY=...  # Get from https://www.pinecone.io/
PINECONE_ENVIRONMENT=us-west1-gcp

# ============================================================================
# EXTERNAL SERVICES
# ============================================================================

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=app-specific-password

# File Storage (AWS S3)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=wellness-ai-storage
AWS_REGION=us-east-1

# ============================================================================
# MONITORING
# ============================================================================

# MLflow
MLFLOW_TRACKING_URI=http://mlflow:5000

# Weights & Biases
WANDB_API_KEY=...  # Get from https://wandb.ai/authorize

# Sentry (Error Tracking)
SENTRY_DSN=https://...@sentry.io/...

# ============================================================================
# FRONTEND
# ============================================================================
BACKEND_URL=http://backend:8000

# ============================================================================
# SECURITY
# ============================================================================
ALLOWED_ORIGINS=http://localhost:8501,https://yourdomain.com
CORS_ALLOWED_ORIGINS=["http://localhost:8501", "https://yourdomain.com"]
```

### Generate Secrets

```bash
# Generate JWT_SECRET_KEY
openssl rand -hex 32

# Generate SECRET_KEY
openssl rand -hex 32
```

---

## Database Setup

### PostgreSQL

**Initialize Schema:**
```bash
docker-compose exec backend python backend/database/init_db.py
```

**Manual Connection:**
```bash
docker-compose exec postgres psql -U wellness_user -d wellness_db
```

**Create Indexes (for performance):**
```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_health_metrics_user_date ON health_metrics(user_id, date);
CREATE INDEX idx_eeg_analyses_user_timestamp ON eeg_analyses(user_id, timestamp);
```

### MongoDB

**Initialize Collections:**
Collections are created automatically on first use.

**Manual Connection:**
```bash
docker-compose exec mongo mongosh -u wellness_user -p secure_password
```

**Create Indexes:**
```javascript
use wellness_db

db.journal_entries.createIndex({ user_id: 1, date: -1 })
db.eeg_raw_data.createIndex({ user_id: 1, timestamp: -1 })
db.chat_messages.createIndex({ user_id: 1, timestamp: -1 })
```

### Neo4j

**Access Neo4j Browser:**
http://localhost:7474

**Credentials:**
- Username: `neo4j`
- Password: (from `.env`)

**Initialize Graph Schema:**
```cypher
// Create constraints
CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT food_name_unique IF NOT EXISTS FOR (f:Food) REQUIRE f.name IS UNIQUE;
CREATE CONSTRAINT supplement_name_unique IF NOT EXISTS FOR (s:Supplement) REQUIRE s.name IS UNIQUE;

// Create indexes
CREATE INDEX user_email IF NOT EXISTS FOR (u:User) ON (u.email);
```

---

## Docker Deployment

### Production Docker Compose

**docker-compose.prod.yml:**

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: wellness_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # MongoDB Database
  mongo:
    image: mongo:6
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
    volumes:
      - mongo_data:/data/db
    restart: unless-stopped
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Neo4j Graph Database
  neo4j:
    image: neo4j:5
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
    volumes:
      - neo4j_data:/data
    restart: unless-stopped

  # FastAPI Backend
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - MONGODB_URL=${MONGODB_URL}
      - REDIS_URL=${REDIS_URL}
      - NEO4J_URI=${NEO4J_URI}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      mongo:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Streamlit Frontend
  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    environment:
      - BACKEND_URL=http://backend:8000
    depends_on:
      - backend
    restart: unless-stopped

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/html:/usr/share/nginx/html:ro
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

  # MLflow Tracking Server
  mlflow:
    image: ghcr.io/mlflow/mlflow:latest
    command: mlflow server --backend-store-uri postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/mlflow --default-artifact-root s3://mlflow-artifacts --host 0.0.0.0
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    depends_on:
      - postgres
    restart: unless-stopped

  # Prometheus Monitoring
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped

  # Grafana Dashboards
  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana-dashboards:/etc/grafana/provisioning/dashboards:ro
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  postgres_data:
  mongo_data:
  redis_data:
  neo4j_data:
  prometheus_data:
  grafana_data:
```

**Deploy:**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

**View Logs:**
```bash
docker-compose -f docker-compose.prod.yml logs -f backend
```

**Scale Services:**
```bash
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

---

## Kubernetes Deployment

### Prerequisites

1. **Kubernetes Cluster:** Use Minikube (local), k3s, or cloud provider (AWS EKS, GCP GKE, Azure AKS)
2. **kubectl:** Configured to connect to your cluster
3. **Helm:** For package management

### 1. Create Namespace

```bash
kubectl create namespace wellness-ai
kubectl config set-context --current --namespace=wellness-ai
```

### 2. Create Secrets

```bash
# Create secrets from .env file
kubectl create secret generic wellness-secrets \
  --from-literal=jwt-secret-key=$(openssl rand -hex 32) \
  --from-literal=postgres-password=$(openssl rand -base64 32) \
  --from-literal=mongo-password=$(openssl rand -base64 32) \
  --from-literal=redis-password=$(openssl rand -base64 32) \
  --from-literal=neo4j-password=$(openssl rand -base64 32) \
  --from-literal=openai-api-key=YOUR_OPENAI_KEY

# Create TLS secret for HTTPS
kubectl create secret tls wellness-tls \
  --cert=path/to/cert.pem \
  --key=path/to/key.pem
```

### 3. Deploy Databases with Helm

**PostgreSQL:**
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgres bitnami/postgresql \
  --set auth.username=wellness_user \
  --set auth.password=<from-secret> \
  --set auth.database=wellness_db \
  --set primary.persistence.size=50Gi
```

**MongoDB:**
```bash
helm install mongo bitnami/mongodb \
  --set auth.rootPassword=<from-secret> \
  --set persistence.size=50Gi
```

**Redis:**
```bash
helm install redis bitnami/redis \
  --set auth.password=<from-secret> \
  --set master.persistence.size=10Gi
```

**Neo4j:**
```bash
helm repo add neo4j https://helm.neo4j.com/neo4j
helm install neo4j neo4j/neo4j \
  --set neo4j.password=<from-secret> \
  --set volumes.data.mode=defaultStorageClass \
  --set volumes.data.defaultStorageClass.requests.storage=20Gi
```

### 4. Deploy Application

**Apply Kubernetes manifests:**

```bash
# Deploy backend
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml

# Deploy frontend
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml

# Deploy ingress (for external access)
kubectl apply -f k8s/ingress.yaml
```

**Example backend-deployment.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: wellness-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/wellness-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://wellness_user:$(POSTGRES_PASSWORD)@postgres:5432/wellness_db"
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: wellness-secrets
              key: jwt-secret-key
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: wellness-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

### 5. Expose Services

**Create Ingress:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: wellness-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - wellnessai.com
    secretName: wellness-tls
  rules:
  - host: wellnessai.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 8501
```

**Apply:**
```bash
kubectl apply -f k8s/ingress.yaml
```

### 6. Verify Deployment

```bash
# Check pods
kubectl get pods

# Check services
kubectl get services

# Check ingress
kubectl get ingress

# View logs
kubectl logs -f deployment/backend
```

### 7. Set Up Horizontal Pod Autoscaling

```bash
kubectl autoscale deployment backend --cpu-percent=70 --min=3 --max=10
kubectl autoscale deployment frontend --cpu-percent=70 --min=2 --max=8
```

---

## Cloud Deployment Options

### AWS (Amazon Web Services)

**Services Used:**
- **EKS (Elastic Kubernetes Service):** Application hosting
- **RDS (Relational Database Service):** PostgreSQL
- **DocumentDB:** MongoDB-compatible
- **ElastiCache:** Redis
- **S3:** File storage
- **CloudFront:** CDN
- **Route 53:** DNS
- **Certificate Manager:** SSL/TLS

**Deployment Steps:**

1. **Create EKS Cluster:**
```bash
eksctl create cluster \
  --name wellness-ai \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.large \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 10 \
  --managed
```

2. **Create RDS PostgreSQL:**
```bash
aws rds create-db-instance \
  --db-instance-identifier wellness-postgres \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --master-username wellness_user \
  --master-user-password <secure-password> \
  --allocated-storage 100
```

3. **Create ElastiCache Redis:**
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id wellness-redis \
  --cache-node-type cache.t3.medium \
  --engine redis \
  --num-cache-nodes 1
```

4. **Deploy to EKS:**
Follow [Kubernetes Deployment](#kubernetes-deployment) steps.

5. **Set Up CloudFront:**
- Create distribution
- Point to EKS load balancer
- Configure SSL certificate
- Enable caching for static assets

**Estimated Monthly Cost:**
- EKS: $75 (control plane)
- EC2 instances: $150 (3x t3.large)
- RDS: $60 (db.t3.medium)
- ElastiCache: $30
- S3: $10-50 (depends on usage)
- **Total: ~$325-365/month**

---

### GCP (Google Cloud Platform)

**Services Used:**
- **GKE (Google Kubernetes Engine):** Application hosting
- **Cloud SQL:** PostgreSQL
- **MongoDB Atlas:** (via marketplace)
- **Memorystore:** Redis
- **Cloud Storage:** File storage
- **Cloud CDN:** Content delivery
- **Cloud DNS:** DNS

**Deployment Steps:**

1. **Create GKE Cluster:**
```bash
gcloud container clusters create wellness-ai \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --enable-autoscaling --min-nodes 3 --max-nodes 10
```

2. **Create Cloud SQL:**
```bash
gcloud sql instances create wellness-postgres \
  --database-version=POSTGRES_14 \
  --tier=db-n1-standard-1 \
  --region=us-central1
```

3. **Deploy to GKE:**
Follow [Kubernetes Deployment](#kubernetes-deployment) steps.

**Estimated Monthly Cost: ~$300-400/month**

---

### Azure

**Services Used:**
- **AKS (Azure Kubernetes Service):** Application hosting
- **Azure Database for PostgreSQL:** Managed PostgreSQL
- **Cosmos DB:** MongoDB API
- **Azure Cache for Redis:** Redis
- **Blob Storage:** File storage
- **Azure CDN:** Content delivery

**Deployment Steps:**

1. **Create AKS Cluster:**
```bash
az aks create \
  --resource-group wellness-rg \
  --name wellness-aks \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys
```

2. **Create PostgreSQL:**
```bash
az postgres server create \
  --resource-group wellness-rg \
  --name wellness-postgres \
  --location eastus \
  --admin-user wellness_user \
  --admin-password <secure-password> \
  --sku-name GP_Gen5_2
```

3. **Deploy to AKS:**
Follow [Kubernetes Deployment](#kubernetes-deployment) steps.

**Estimated Monthly Cost: ~$350-450/month**

---

## SSL/TLS Configuration

### Let's Encrypt with Cert-Manager (Kubernetes)

1. **Install Cert-Manager:**
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

2. **Create ClusterIssuer:**
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@wellnessai.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

```bash
kubectl apply -f cluster-issuer.yaml
```

3. **Update Ingress:**
Add annotation to Ingress:
```yaml
metadata:
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
```

Certificate will be auto-generated and renewed.

---

### Manual SSL (Nginx)

1. **Obtain Certificate:**
```bash
sudo certbot certonly --standalone -d wellnessai.com -d www.wellnessai.com
```

2. **Configure Nginx:**
```nginx
server {
    listen 443 ssl http2;
    server_name wellnessai.com;

    ssl_certificate /etc/letsencrypt/live/wellnessai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wellnessai.com/privkey.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;

    # Proxy to frontend
    location / {
        proxy_pass http://frontend:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Proxy to backend API
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name wellnessai.com;
    return 301 https://$server_name$request_uri;
}
```

3. **Reload Nginx:**
```bash
docker-compose exec nginx nginx -s reload
```

---

## Monitoring & Logging

### Prometheus + Grafana

**Access Grafana:**
http://localhost:3000

**Default Credentials:**
- Username: `admin`
- Password: (from `.env`)

**Import Dashboards:**
1. Go to Dashboards → Import
2. Upload JSON from `monitoring/grafana-dashboards/`
3. Select Prometheus data source

**Key Metrics:**
- API request rate
- Response times (P50, P95, P99)
- Error rates
- Database connection pool
- EEG analysis queue length
- User activity

### Logging with ELK Stack (Optional)

**Install Elasticsearch, Logstash, Kibana:**

```yaml
# Add to docker-compose.prod.yml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.10.0
  environment:
    - discovery.type=single-node
  volumes:
    - es_data:/usr/share/elasticsearch/data

kibana:
  image: docker.elastic.co/kibana/kibana:8.10.0
  depends_on:
    - elasticsearch
  ports:
    - "5601:5601"
```

**Configure Backend to Send Logs:**

```python
import logging
from elasticache import ElasticsearchHandler

handler = ElasticsearchHandler('elasticsearch', 9200)
logger.addHandler(handler)
```

**Access Kibana:**
http://localhost:5601

---

## Backup & Recovery

### Database Backups

**PostgreSQL:**

**Automated Daily Backup:**
```bash
#!/bin/bash
# backup-postgres.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups/postgres
FILENAME=wellness_db_$DATE.sql.gz

docker-compose exec -T postgres pg_dump -U wellness_user wellness_db | gzip > $BACKUP_DIR/$FILENAME

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

**Cron Job:**
```bash
0 2 * * * /path/to/backup-postgres.sh
```

**Restore:**
```bash
gunzip < backup.sql.gz | docker-compose exec -T postgres psql -U wellness_user -d wellness_db
```

---

**MongoDB:**

**Backup:**
```bash
docker-compose exec mongo mongodump --username wellness_user --password <password> --authenticationDatabase admin --out /backup
```

**Restore:**
```bash
docker-compose exec mongo mongorestore --username wellness_user --password <password> --authenticationDatabase admin /backup
```

---

**Cloud Backups (AWS S3):**

```bash
# Sync backups to S3
aws s3 sync /backups/postgres s3://wellness-backups/postgres/
aws s3 sync /backups/mongo s3://wellness-backups/mongo/
```

---

## Scaling

### Horizontal Scaling (Kubernetes)

**Auto-scaling based on CPU:**
```bash
kubectl autoscale deployment backend --cpu-percent=70 --min=3 --max=10
```

**Auto-scaling based on custom metrics (requests/sec):**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
```

### Vertical Scaling

**Increase pod resources:**
```yaml
resources:
  requests:
    memory: "4Gi"
    cpu: "2000m"
  limits:
    memory: "8Gi"
    cpu: "4000m"
```

### Database Scaling

**PostgreSQL Read Replicas:**
- Create read replicas for queries
- Route analytics queries to replicas
- Keep writes on primary

**MongoDB Sharding:**
- Shard by user_id for horizontal scaling
- Use MongoDB Atlas for managed sharding

**Redis Cluster:**
- Use Redis Cluster mode for multi-node setup
- Distribute keys across nodes

---

## CI/CD Pipeline

### GitHub Actions

**`.github/workflows/deploy.yml`:**

```yaml
name: Deploy Wellness AI

on:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run tests
        run: |
          pytest tests/ -v

      - name: Run linter
        run: |
          flake8 backend/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker images
        run: |
          docker build -t wellness-backend:${{ github.sha }} -f backend/Dockerfile .
          docker build -t wellness-frontend:${{ github.sha }} -f frontend/Dockerfile .

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker tag wellness-backend:${{ github.sha }} yourusername/wellness-backend:latest
          docker push yourusername/wellness-backend:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/backend backend=yourusername/wellness-backend:${{ github.sha }}
          kubectl rollout status deployment/backend
```

---

## Security Hardening

### 1. Network Security

**Firewall Rules:**
- Only expose ports 80 (HTTP) and 443 (HTTPS) to public
- Database ports (5432, 27017, 6379, 7687) only accessible within cluster

**Kubernetes Network Policies:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-network-policy
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
```

### 2. Secrets Management

**Use Kubernetes Secrets or HashiCorp Vault:**
```bash
# Seal secrets with Sealed Secrets
kubeseal --format=yaml < secret.yaml > sealed-secret.yaml
kubectl apply -f sealed-secret.yaml
```

### 3. Enable RBAC

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: wellness-app-role
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list"]
```

### 4. Regular Security Scans

**Scan Docker images:**
```bash
docker scan wellness-backend:latest
```

**Scan dependencies:**
```bash
safety check -r requirements.txt
```

---

## Troubleshooting

### Backend Not Starting

**Check logs:**
```bash
docker-compose logs backend
kubectl logs deployment/backend
```

**Common issues:**
- Database not reachable → Check `DATABASE_URL`
- Missing API keys → Check `.env` or secrets
- Port already in use → Change port or stop conflicting service

### Database Connection Errors

**Test connection:**
```bash
# PostgreSQL
docker-compose exec backend python -c "from backend.database.postgres import engine; print(engine.connect())"

# MongoDB
docker-compose exec backend python -c "from backend.database.mongo import client; print(client.server_info())"
```

### Frontend Can't Reach Backend

**Check BACKEND_URL:**
- In Docker: Should be `http://backend:8000` (service name)
- Local development: Should be `http://localhost:8000`

### SSL Certificate Issues

**Renew Let's Encrypt:**
```bash
docker-compose exec nginx certbot renew
```

**Check certificate expiry:**
```bash
echo | openssl s_client -servername wellnessai.com -connect wellnessai.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Out of Memory

**Increase Docker memory limit:**
Docker Desktop → Settings → Resources → Memory: 8GB+

**Kubernetes pod memory:**
```bash
kubectl top pods
kubectl describe pod <pod-name>
```

Increase in deployment:
```yaml
resources:
  limits:
    memory: "4Gi"
```

---

## Post-Deployment Checklist

- [ ] All services are running and healthy
- [ ] Database connections are working
- [ ] HTTPS is enabled and certificate is valid
- [ ] Monitoring dashboards are accessible
- [ ] Backups are scheduled and tested
- [ ] Auto-scaling is configured
- [ ] CI/CD pipeline is set up
- [ ] Security scans are passing
- [ ] API rate limiting is enabled
- [ ] Logging is centralized
- [ ] Alerts are configured (Slack, PagerDuty, etc.)
- [ ] Documentation is updated
- [ ] DNS records are correct
- [ ] CDN is configured (if using)
- [ ] Load testing completed

---

## Support & Resources

**Documentation:**
- Official Docs: https://docs.wellnessai.com
- API Reference: https://docs.wellnessai.com/api
- Kubernetes Guide: https://kubernetes.io/docs

**Community:**
- GitHub Issues: https://github.com/your-org/Wellnessapp/issues
- Discord: https://discord.gg/wellness-ai
- Stack Overflow: Tag `wellness-ai`

**Contact:**
- DevOps Support: devops@wellnessai.com
- Security Issues: security@wellnessai.com

---

**Deployment Guide Version:** 1.0.0
**Last Updated:** November 16, 2025

**Happy Deploying! 🚀**
