# 🚀 Complete Setup Guide

This guide will help you set up and run the Wellness AI Platform from scratch.

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Steps](#installation-steps)
3. [Database Setup](#database-setup)
4. [Running the Application](#running-the-application)
5. [Testing](#testing)
6. [Common Issues](#common-issues)

---

## 💻 System Requirements

### Minimum Requirements
- **OS**: Linux, macOS, or Windows (with WSL2)
- **RAM**: 8GB+
- **Storage**: 10GB free space
- **Python**: 3.9 or higher
- **Docker**: 20.10+
- **Docker Compose**: 1.29+

### Recommended
- **RAM**: 16GB+
- **GPU**: NVIDIA GPU with CUDA support (for faster ML inference)
- **CPU**: 4+ cores

---

## 📦 Installation Steps

### Step 1: Clone the Repository

```bash
git clone https://github.com/Srujan29112001/Wellnessapp.git
cd Wellnessapp
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows
```

### Step 3: Install Dependencies

```bash
# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# For development (optional)
pip install -r requirements-dev.txt
```

### Step 4: Set Up Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit the .env file with your configuration
nano .env  # or use your preferred editor
```

**Required variables**:
```env
# Database URLs (default for Docker Compose)
DATABASE_URL=postgresql+asyncpg://wellness:wellness@localhost:5432/wellness_db
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=wellness
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=wellness123
REDIS_URL=redis://localhost:6379

# Optional: OpenAI API (for GPT-based coach)
OPENAI_API_KEY=sk-your-key-here  # Leave empty to use local models

# Security
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000

# Application
DEBUG=True
LOG_LEVEL=INFO
```

---

## 🗄️ Database Setup

### Option 1: Using Docker Compose (Recommended)

This starts all required databases automatically:

```bash
# Start all services
docker-compose up -d

# Check that all containers are running
docker-compose ps

# View logs
docker-compose logs -f
```

**Services started**:
- PostgreSQL (port 5432)
- MongoDB (port 27017)
- Neo4j (ports 7474, 7687)
- Redis (port 6379)
- FastAPI backend (port 8000)
- Streamlit frontend (port 8501)
- MLflow (port 5000)
- Prometheus (port 9090)
- Grafana (port 3000)

### Option 2: Manual Setup (Advanced)

If you prefer to run databases locally without Docker:

#### PostgreSQL

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib  # Ubuntu/Debian
# OR
brew install postgresql  # macOS

# Start PostgreSQL
sudo service postgresql start  # Linux
brew services start postgresql  # macOS

# Create database and user
sudo -u postgres psql
```

```sql
CREATE DATABASE wellness_db;
CREATE USER wellness WITH PASSWORD 'wellness';
GRANT ALL PRIVILEGES ON DATABASE wellness_db TO wellness;
\q
```

#### MongoDB

```bash
# Install MongoDB
sudo apt-get install mongodb  # Ubuntu/Debian
brew install mongodb-community  # macOS

# Start MongoDB
sudo service mongodb start  # Linux
brew services start mongodb-community  # macOS
```

#### Neo4j

```bash
# Download from https://neo4j.com/download/
# Or use Docker:
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/wellness123 \
  neo4j:latest
```

#### Redis

```bash
# Install Redis
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis  # macOS

# Start Redis
sudo service redis-server start  # Linux
brew services start redis  # macOS
```

---

## 🔧 Initialize the Application

### Step 1: Initialize Databases

```bash
# Initialize PostgreSQL tables
python -c "
from backend.database.postgres import init_db
import asyncio
asyncio.run(init_db())
"

# Initialize MongoDB indexes
python -c "
from backend.database.mongo import init_mongo
import asyncio
asyncio.run(init_mongo())
"

# Initialize Neo4j knowledge graph
python -c "
from backend.services.graph_rag_service import graph_rag
import asyncio
asyncio.run(graph_rag.initialize_knowledge_graph())
"
```

### Step 2: Create a Demo User

```bash
python -c "
from backend.services.user_service import UserService
from backend.database.postgres import AsyncSessionLocal
import asyncio

async def create_demo_user():
    async with AsyncSessionLocal() as db:
        await UserService.create_user(
            db,
            email='demo@wellness.ai',
            name='Demo User',
            password='demo123'
        )
        print('Demo user created: demo@wellness.ai / demo123')

asyncio.run(create_demo_user())
"
```

### Step 3: (Optional) Train EEG Models

```bash
# Train EEG classifiers on sample data
python ml/eeg_analysis/train_pipeline.py

# This will:
# 1. Generate synthetic EEG training data
# 2. Train ANN and SNN classifiers
# 3. Save models to models/eeg/
# 4. Log experiments to MLflow

# Check training results
# Open http://localhost:5000 (MLflow UI)
```

---

## ▶️ Running the Application

### Option 1: Using Docker Compose

```bash
# Start all services
docker-compose up -d

# Access the application:
# - Streamlit Dashboard: http://localhost:8501
# - API Docs: http://localhost:8000/docs
# - GraphQL: http://localhost:8000/graphql
```

### Option 2: Manual Start

#### Terminal 1: Start Backend

```bash
# Activate virtual environment
source venv/bin/activate

# Start FastAPI server
cd backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2: Start Frontend

```bash
# Activate virtual environment
source venv/bin/activate

# Start Streamlit
streamlit run frontend/app.py --server.port 8501
```

#### Terminal 3: Start MLflow (Optional)

```bash
# Activate virtual environment
source venv/bin/activate

# Start MLflow server
mlflow server --host 0.0.0.0 --port 5000
```

---

## 🧪 Testing the Application

### Quick Health Check

```bash
# Check API health
curl http://localhost:8000/health

# Expected: {"status": "healthy"}
```

### Test API Endpoints

#### 1. Health Metrics

```bash
# Log health data
curl -X POST http://localhost:8000/api/health \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-01-15",
    "steps": 8500,
    "sleep_hours": 7.5,
    "calories_burned": 420
  }'

# Get health metrics
curl http://localhost:8000/api/health
```

#### 2. AI Coach

```bash
# Chat with AI coach
curl -X POST http://localhost:8000/api/coach/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I feel stressed and tired",
    "include_context": true
  }'
```

#### 3. Meals

```bash
# Log a meal
curl -X POST http://localhost:8000/api/meals \
  -H "Content-Type: application/json" \
  -d '{
    "meal_type": "lunch",
    "food_items": ["Grilled chicken", "Salad"],
    "calories": 450,
    "protein_g": 35
  }'
```

### Run Automated Tests

```bash
# Unit tests
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# All tests with coverage
pytest --cov=backend --cov=ml tests/
```

---

## 🎨 Access the Dashboard

### Streamlit Dashboard

Open http://localhost:8501 in your browser.

**Features**:
- 📊 Dashboard: Overview of health metrics
- 🧠 EEG Analysis: Upload and analyze EEG data
- 💬 AI Coach: Chat with wellness AI
- 🥗 Nutrition: Log meals and view trends
- 💊 Supplements: Track supplement intake
- ⚙️ Settings: Configure preferences

### API Documentation

Open http://localhost:8000/docs (Swagger UI) or http://localhost:8000/redoc

### GraphQL Playground

Open http://localhost:8000/graphql

**Example Query**:
```graphql
query {
  healthMetrics(userId: "demo_user", limit: 7) {
    date
    steps
    sleepHours
    stressLevel
  }
}
```

---

## 🛠️ Common Issues & Solutions

### Issue 1: Port Already in Use

```bash
# Check what's using the port
lsof -i :8000  # Replace with your port

# Kill the process
kill -9 <PID>

# Or use different ports in docker-compose.yml
```

### Issue 2: Database Connection Failed

```bash
# Check if databases are running
docker-compose ps

# Restart databases
docker-compose restart postgres mongodb neo4j redis

# Check logs
docker-compose logs postgres
```

### Issue 3: Import Errors

```bash
# Ensure you're in the project root and venv is activated
source venv/bin/activate
export PYTHONPATH=/home/user/Wellnessapp:$PYTHONPATH

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue 4: Neo4j Connection Timeout

```bash
# Increase timeout in settings
# Edit config/settings.py or .env

# Or wait for Neo4j to fully start (can take 30-60 seconds)
docker-compose logs -f neo4j
```

### Issue 5: EEG Models Not Found

```bash
# Train models first
python ml/eeg_analysis/train_pipeline.py

# Check models directory
ls -la models/eeg/

# Should see: ann_model.pth, snn_model.pth
```

---

## 🔐 Security Configuration (Production)

### 1. Change Default Credentials

```env
# Update .env with strong passwords
DATABASE_URL=postgresql+asyncpg://wellness:STRONG_PASSWORD_HERE@...
NEO4J_PASSWORD=STRONG_PASSWORD_HERE
JWT_SECRET_KEY=$(openssl rand -hex 32)
```

### 2. Enable HTTPS

```bash
# Use a reverse proxy (nginx, traefik)
# Or configure FastAPI with SSL certificates
```

### 3. Set DEBUG=False

```env
DEBUG=False
LOG_LEVEL=WARNING
```

---

## 📊 Monitoring

### Prometheus

Access: http://localhost:9090

**Useful Queries**:
```promql
# API request rate
rate(http_requests_total[5m])

# Database query time
histogram_quantile(0.95, db_query_duration_seconds_bucket)
```

### Grafana

Access: http://localhost:3000 (admin/admin)

**Import Dashboards**:
1. Go to Dashboards → Import
2. Upload JSON from `monitoring/grafana/dashboards/`

---

## 🚀 Next Steps

1. **Explore the API**: Try different endpoints via Swagger UI
2. **Upload EEG Data**: Test EEG analysis with sample data
3. **Chat with AI**: Have a conversation with the wellness coach
4. **Track Health**: Log daily metrics and view trends
5. **Customize**: Modify knowledge base, add custom supplements
6. **Deploy**: Follow deployment guide for production setup

---

## 📚 Additional Resources

- **Project Documentation**: See README.md
- **API Reference**: http://localhost:8000/docs
- **Architecture**: See ARCHITECTURE.md (coming soon)
- **Contributing**: See CONTRIBUTING.md (coming soon)

---

## 🆘 Getting Help

If you encounter issues not covered here:

1. Check existing [GitHub Issues](https://github.com/Srujan29112001/Wellnessapp/issues)
2. Create a new issue with:
   - Steps to reproduce
   - Error messages
   - System info (OS, Python version, Docker version)
3. Join discussions: [GitHub Discussions](https://github.com/Srujan29112001/Wellnessapp/discussions)

---

**Happy Wellness Tracking! 🌟**
