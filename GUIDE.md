# 📘 Wellness AI Platform - Complete Guide

> **Production-ready AI-powered holistic wellness platform with EEG analysis, conversational coaching, and personalized health recommendations.**

---

## 📑 Table of Contents

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Using the Platform](#using-the-platform)
- [API Reference](#api-reference)
- [Development](#development)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

---

## 🎯 Introduction

### What is Wellness AI?

Wellness AI is a comprehensive holistic health platform that combines:

- **🧠 EEG Brain Signal Analysis** - Real-time mental state detection (stress, focus, relaxation)
- **🤖 AI Wellness Coach** - LLM-powered conversational guidance with long-term memory
- **📊 Multi-Modal Health Tracking** - Sleep, activity, nutrition, voice, and biometrics
- **🌿 Ayurvedic Integration** - Traditional dosha assessment and personalized recommendations
- **🔬 ML-Powered Features** - Voice emotion detection, food recognition, supplement OCR
- **📚 Knowledge Graph** - GraphRAG for complex health reasoning over curated wellness knowledge

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Frontend (Streamlit)                   │
│  Dashboard | EEG | Coach | Metrics | Nutrition | Settings │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│           Backend API (FastAPI + GraphQL)                │
│  Authentication | REST Endpoints | GraphQL Mutations      │
└──────┬──────────────────────────────────────┬────────────┘
       │                                      │
┌──────▼────────────────────┐  ┌─────────────▼────────────┐
│   ML Processing Layer     │  │  Knowledge & Reasoning   │
│                           │  │                          │
│  • EEG Analysis (CNN)     │  │  • GraphRAG (Neo4j)      │
│  • Voice Emotion (MFCC)   │  │  • RAG (ChromaDB)        │
│  • Food Recognition (ViT) │  │  • LLM Coach (LangChain) │
│  • OCR (Tesseract)        │  │  • Vector Embeddings     │
└──────┬────────────────────┘  └─────────────┬────────────┘
       │                                      │
┌──────▼──────────────────────────────────────▼────────────┐
│                   Data Storage Layer                      │
│                                                           │
│  PostgreSQL (structured) | MongoDB (unstructured)        │
│  Redis (cache/sessions) | Neo4j (knowledge graph)        │
└───────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Streamlit, Plotly, Matplotlib |
| **Backend API** | FastAPI, Strawberry GraphQL, Uvicorn |
| **AI/ML** | PyTorch, scikit-learn, LangChain, Transformers |
| **Signal Processing** | MNE-Python, SciPy, NumPy |
| **Computer Vision** | torchvision, OpenCV, EasyOCR |
| **Audio** | librosa, SpeechRecognition |
| **Databases** | PostgreSQL, MongoDB, Redis, Neo4j |
| **Vector DB** | ChromaDB, sentence-transformers |
| **MLOps** | MLflow, Airflow, Prometheus, Grafana |
| **Deployment** | Docker, Kubernetes |

---

## 🔧 Prerequisites

### Required Software

| Software | Minimum Version | Check Command |
|----------|----------------|---------------|
| Python | 3.9+ | `python3 --version` |
| pip | Latest | `pip3 --version` |
| Git | 2.0+ | `git --version` |

### For Docker Setup (Recommended)

| Software | Minimum Version | Check Command |
|----------|----------------|---------------|
| Docker | 20.10+ | `docker --version` |
| Docker Compose | 1.29+ | `docker-compose --version` |

### System Requirements

- **Minimum**: 8GB RAM, 10GB disk space, 2 CPU cores
- **Recommended**: 16GB RAM, 50GB disk space, 4 CPU cores
- **For Training**: NVIDIA GPU with CUDA (optional but recommended)

### Optional API Keys

For full LLM functionality, you can add:
- **OpenAI API Key** - For GPT-4 powered coaching
- **Anthropic API Key** - For Claude powered coaching
- **Weights & Biases** - For ML experiment tracking
- **Pinecone** - Alternative vector database

---

## 📦 Installation

### Option 1: Quick Install with Docker (Recommended)

**Step 1: Clone Repository**
```bash
git clone https://github.com/Srujan29112001/Wellnessapp.git
cd Wellnessapp
```

**Step 2: Configure Environment**
```bash
# .env file already created from template
# Edit to add your API keys (optional)
nano .env

# Add (optional):
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
```

**Step 3: Start Services**
```bash
# Start all services in background
docker-compose up -d

# Check status
docker-compose ps
```

**Step 4: Initialize Databases**
```bash
# Install Python dependencies for init script
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Initialize databases and load knowledge bases
python backend/database/init_db.py
```

**Step 5: Verify Installation**
```bash
# Test backend health
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","service":"Wellness AI","version":"0.1.0"}

# Access frontend
open http://localhost:8501
```

---

### Option 2: Local Development Install

**Step 1: Clone Repository**
```bash
git clone https://github.com/Srujan29112001/Wellnessapp.git
cd Wellnessapp
```

**Step 2: Create Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

**Step 3: Install Python Dependencies**
```bash
pip install -r requirements.txt

# This installs 116 packages including:
# - FastAPI, uvicorn, strawberry-graphql
# - PyTorch, transformers, scikit-learn
# - LangChain, chromadb, sentence-transformers
# - MNE, librosa, opencv-python
# - SQLAlchemy, pymongo, redis, neo4j
# - Streamlit, plotly, matplotlib
# And many more...
```

**Step 4: Install Databases**

<details>
<summary><b>PostgreSQL</b></summary>

```bash
# macOS
brew install postgresql@14
brew services start postgresql@14

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql-14
sudo systemctl start postgresql

# Windows
# Download installer from postgresql.org

# Create database
createdb wellness_db
psql -d postgres -c "CREATE USER wellness_user WITH PASSWORD 'wellness_password';"
psql -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE wellness_db TO wellness_user;"
```
</details>

<details>
<summary><b>MongoDB</b></summary>

```bash
# macOS
brew tap mongodb/brew
brew install mongodb-community@6.0
brew services start mongodb-community@6.0

# Ubuntu/Debian
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod

# Windows
# Download installer from mongodb.com

# Verify
mongosh --eval "db.version()"
```
</details>

<details>
<summary><b>Redis</b></summary>

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Windows
# Use Docker or WSL

# Verify
redis-cli ping  # Should return PONG
```
</details>

<details>
<summary><b>Neo4j (Optional - for GraphRAG)</b></summary>

```bash
# macOS
brew install neo4j
neo4j start

# Ubuntu/Debian
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt-get update
sudo apt-get install neo4j
sudo systemctl start neo4j

# Set initial password
cypher-shell -u neo4j -p neo4j
# Then run: ALTER CURRENT USER SET PASSWORD FROM 'neo4j' TO 'wellness_password';

# Access browser interface
open http://localhost:7474
```
</details>

**Step 5: Configure Environment**
```bash
# Environment variables are in .env file
cat .env

# Verify database URLs are correct:
DATABASE_URL=postgresql://wellness_user:wellness_password@localhost:5432/wellness_db
MONGODB_URL=mongodb://localhost:27017/wellness_mongo
REDIS_HOST=localhost
NEO4J_URI=bolt://localhost:7687
```

**Step 6: Initialize Databases**
```bash
python backend/database/init_db.py
```

Expected output:
```
INFO - Starting Database Initialization
INFO - Initializing PostgreSQL...
INFO - PostgreSQL tables created successfully
INFO - Initializing MongoDB...
INFO - Connected to MongoDB: wellness_mongo
INFO - MongoDB indexes created successfully
INFO - Creating demo user...
INFO - Created demo user: <uuid>
INFO - Created user context in MongoDB
INFO - Seeding Neo4j knowledge graph...
INFO - Cleared existing Neo4j data
INFO - Seeded Neo4j knowledge graph successfully
INFO - Database Initialization Complete
```

---

## 🚀 Running the Application

### With Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down
```

### Local Development

**Terminal 1 - Backend API:**
```bash
cd /path/to/Wellnessapp
source venv/bin/activate
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend UI:**
```bash
cd /path/to/Wellnessapp
source venv/bin/activate
streamlit run frontend/app.py --server.port 8501
```

**Terminal 3 - MLflow (Optional):**
```bash
cd /path/to/Wellnessapp
source venv/bin/activate
mlflow ui --port 5000
```

### Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| 🎨 **Frontend** | http://localhost:8501 | Main user interface |
| 📡 **API Docs** | http://localhost:8000/docs | Interactive API documentation (Swagger) |
| 🔮 **GraphQL** | http://localhost:8000/graphql | GraphQL playground |
| 💚 **Health** | http://localhost:8000/health | API health check |
| 🕸️ **Neo4j** | http://localhost:7474 | Knowledge graph browser |
| 🔬 **MLflow** | http://localhost:5000 | ML experiment tracking |
| 📊 **Grafana** | http://localhost:3000 | Monitoring dashboards |
| 📈 **Prometheus** | http://localhost:9090 | Metrics collection |

---

## 📱 Using the Platform

### Frontend Pages

#### 1. 🏠 Dashboard
**Purpose**: Overview of your health status and trends

**Features**:
- Health score summary
- Recent EEG analysis results
- Key metric trends (sleep, stress, mood)
- Quick actions and recommendations

**How to Use**:
1. Navigate to Dashboard (home page)
2. View your health summary cards
3. Check trend charts for patterns
4. Click on metrics for detailed views

---

#### 2. 🧠 EEG Analysis
**Purpose**: Upload and analyze brain signal data

**Features**:
- EEG file upload (CSV format)
- Real-time signal processing
- Mental state classification (stress, focus, relaxation, drowsiness)
- Frequency band analysis (Delta, Theta, Alpha, Beta, Gamma)
- Recommendations based on brain state

**How to Use**:
1. Go to "🧠 EEG Analysis" page
2. Click "Upload EEG File"
3. Select CSV file with EEG data (14 channels @ 256 Hz)
4. View analysis results:
   - Stress level (0-100%)
   - Focus level (0-100%)
   - Relaxation level (0-100%)
   - Dominant brain wave
   - Mental state classification
5. Review personalized recommendations

**Expected Data Format**:
```csv
timestamp,AF3,F7,F3,FC5,T7,P7,O1,O2,P8,T8,FC6,F4,F8,AF4
0.0,4278.97,4302.05,4292.31,...
0.00390625,4279.49,4301.54,4293.33,...
```

---

#### 3. 💬 AI Coach
**Purpose**: Chat with AI wellness coach for guidance

**Features**:
- Natural language conversation
- Context-aware responses
- Evidence-based recommendations
- Citations from wellness knowledge base
- Long-term memory of your health journey
- Personalized to your dosha and goals

**How to Use**:
1. Go to "💬 AI Coach" page
2. Type your question or concern:
   - "I'm feeling stressed and can't sleep"
   - "What foods are good for my dosha?"
   - "How can I improve my focus?"
3. Review coach's response
4. Ask follow-up questions
5. View recommended interventions

**Example Conversations**:
```
You: I'm having trouble sleeping and feeling anxious

Coach: I understand sleep difficulties and anxiety can be challenging.
Based on your Vata-Pitta dosha and recent EEG data showing elevated
stress (72%), here are evidence-based recommendations:

1. Evening Routine:
   - Stop screen time 2 hours before bed
   - Practice 4-7-8 breathing (inhale 4, hold 7, exhale 8)
   - Drink chamomile tea

2. Supplements:
   - Magnesium glycinate (400mg before bed)
   - L-theanine (200mg for calming)

3. Ayurvedic Approach:
   - Warm sesame oil foot massage
   - Avoid cold, raw foods in evening

Would you like specific meditation guidance?
```

---

#### 4. 📊 Health Metrics
**Purpose**: Log and track daily health data

**Features**:
- Log multiple metrics:
  - Sleep hours and quality
  - Steps and activity
  - Mood (1-10 scale)
  - Energy level (1-10)
  - Stress level (1-10)
  - Water intake
  - Weight
- Trend visualization
- Correlation analysis
- Export data

**How to Use**:
1. Go to "📊 Health Metrics" page
2. Fill in today's metrics
3. Click "Log Metrics"
4. View historical trends
5. Analyze correlations (e.g., sleep vs energy)

---

#### 5. 🍎 Nutrition
**Purpose**: Track meals and get dietary recommendations

**Features**:
- Manual meal logging
- Food image recognition
- Nutritional breakdown
- Calorie tracking
- Macronutrient distribution
- Dosha-appropriate food suggestions

**How to Use**:
1. Go to "🍎 Nutrition" page
2. Log a meal:
   - **Option A**: Upload food photo → AI identifies food
   - **Option B**: Manually enter meal details
3. View nutritional analysis
4. Track daily intake vs goals
5. Get personalized food recommendations

---

#### 6. 💊 Supplements
**Purpose**: Research supplements and track intake

**Features**:
- Supplement database search (50+ supplements)
- Detailed profiles:
  - Benefits and mechanisms
  - Recommended dosages
  - Side effects
  - Contraindications
  - Drug interactions
  - Scientific evidence
- OCR label scanning
- Personal supplement log
- Interaction checker

**How to Use**:
1. Go to "💊 Supplements" page
2. Search supplement name
3. View detailed profile
4. Scan product label (OCR):
   - Upload label photo
   - Extract ingredients and dosages
5. Log supplements you're taking
6. Check for interactions

---

#### 7. ⚙️ Settings
**Purpose**: Manage profile and preferences

**Features**:
- User profile management
- Dosha assessment questionnaire
- Health goals setup
- Dietary restrictions
- Medical conditions
- Notification preferences
- Privacy settings
- Export personal data

**How to Use**:
1. Go to "⚙️ Settings" page
2. Complete profile information
3. Take Ayurvedic Dosha Assessment:
   - Answer 30 questions
   - Get dosha type (Vata, Pitta, Kapha, or combination)
   - View characteristics
4. Set health goals
5. Configure preferences

---

## 🔌 API Reference

### REST API Endpoints

Base URL: `http://localhost:8000/api/v1`

#### Authentication
```http
POST /auth/register
POST /auth/login
POST /auth/refresh
GET  /auth/me
```

#### EEG Analysis
```http
POST   /eeg/upload          # Upload EEG file
GET    /eeg/analysis/:id    # Get analysis by ID
GET    /eeg/history         # Get user's EEG history
POST   /eeg/realtime        # Real-time streaming analysis
```

#### AI Coach
```http
POST   /coach/chat          # Send message to coach
GET    /coach/history       # Get chat history
POST   /coach/feedback      # Rate coach response
```

#### Health Metrics
```http
POST   /health/log          # Log health metrics
GET    /health/metrics      # Get metrics history
GET    /health/trends       # Get trend analysis
GET    /health/correlations # Correlation analysis
```

#### Voice Analysis
```http
POST   /voice/analyze       # Analyze voice recording
GET    /voice/history       # Get voice analysis history
```

#### Food Recognition
```http
POST   /food/recognize      # Upload food image
POST   /food/ocr-supplement # OCR supplement label
GET    /food/nutrition/:id  # Get nutrition data
```

#### Recommendations
```http
POST   /recommendations/generate  # Generate recommendations
GET    /recommendations/history   # Get past recommendations
PUT    /recommendations/:id/feedback  # Rate recommendation
```

#### Supplements
```http
GET    /supplements/search  # Search supplement database
GET    /supplements/:id     # Get supplement details
POST   /supplements/check-interactions  # Check interactions
```

#### Wearables
```http
POST   /wearables/fitbit/connect       # Connect Fitbit
POST   /wearables/garmin/connect       # Connect Garmin
POST   /wearables/apple-health/upload  # Upload Apple Health data
GET    /wearables/metrics              # Get wearable metrics
```

### API Examples

#### Example 1: Chat with AI Coach

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/coach/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I feel stressed and have trouble sleeping",
    "user_id": "demo_user",
    "include_context": true
  }'
```

**Response:**
```json
{
  "message": "I understand sleep difficulties can be challenging...",
  "recommendations": [
    {
      "type": "lifestyle",
      "intervention": "Practice 4-7-8 breathing before bed",
      "reason": "Activates parasympathetic nervous system",
      "evidence": "Harvard Medical School study on breathing techniques"
    },
    {
      "type": "supplement",
      "intervention": "Magnesium glycinate 400mg",
      "reason": "Promotes relaxation and sleep quality",
      "evidence": "PMID: 23853635"
    }
  ],
  "context_used": ["recent_eeg_stress_high", "dosha_vata_imbalance"],
  "timestamp": "2024-01-15T20:30:00Z"
}
```

#### Example 2: Upload EEG Data

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/eeg/upload" \
  -F "file=@eeg_data.csv" \
  -F "user_id=demo_user"
```

**Response:**
```json
{
  "analysis_id": "eeg_abc123",
  "user_id": "demo_user",
  "timestamp": "2024-01-15T20:30:00Z",
  "mental_state": {
    "stress_level": 0.72,
    "focus_level": 0.45,
    "relaxation_level": 0.23,
    "drowsiness_level": 0.18,
    "dominant_state": "stressed"
  },
  "band_powers": {
    "delta": 23.5,
    "theta": 18.2,
    "alpha": 15.8,
    "beta": 28.9,
    "gamma": 13.6
  },
  "dominant_band": "beta",
  "recommendations": [
    "High beta activity detected. Consider taking a break.",
    "Practice deep breathing to reduce stress.",
    "Avoid caffeine for the next 2 hours."
  ]
}
```

#### Example 3: Get Personalized Recommendations

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user"
  }'
```

**Response:**
```json
{
  "user_id": "demo_user",
  "generated_at": "2024-01-15T20:30:00Z",
  "recommendations": [
    {
      "category": "sleep",
      "priority": "high",
      "intervention": "Establish consistent sleep schedule",
      "reason": "Sleep duration varies by 3+ hours. Consistency improves quality.",
      "evidence": "Sleep Research Society guidelines",
      "actionable_steps": [
        "Set bedtime alarm for 10:30 PM",
        "Create wind-down routine starting 9:30 PM",
        "Avoid screens after 9:00 PM"
      ]
    },
    {
      "category": "nutrition",
      "priority": "medium",
      "intervention": "Increase warm, cooked foods",
      "reason": "Vata dosha imbalance indicated by anxiety and irregular digestion",
      "evidence": "Ayurvedic principles for Vata pacification",
      "foods_to_add": ["Oatmeal", "Soup", "Cooked vegetables", "Ghee"],
      "foods_to_reduce": ["Raw salads", "Cold drinks", "Dry crackers"]
    }
  ],
  "health_score": 72,
  "trending_better": ["energy_level", "mood"],
  "trending_worse": ["sleep_quality", "stress_level"]
}
```

### GraphQL API

Access playground: http://localhost:8000/graphql

**Example Query:**
```graphql
query GetHealthData {
  user(id: "demo_user") {
    id
    name
    doshaType
    healthGoals

    healthMetrics(limit: 30) {
      date
      sleepHours
      stressLevel
      mood
      steps
    }

    eegAnalyses(limit: 10) {
      timestamp
      stressLevel
      focusLevel
      mentalState
      recommendations
    }

    recommendations(limit: 5) {
      category
      intervention
      priority
      reason
    }
  }
}
```

**Example Mutation:**
```graphql
mutation LogMetrics {
  logHealthMetrics(
    userId: "demo_user"
    date: "2024-01-15"
    sleepHours: 7.5
    stressLevel: 4
    mood: 7
    energyLevel: 6
    steps: 8500
  ) {
    id
    date
    sleepHours
  }
}
```

---

## 💻 Development

### Project Structure

```
Wellnessapp/
├── backend/
│   ├── api/
│   │   ├── endpoints/      # REST endpoints
│   │   │   ├── auth.py
│   │   │   ├── eeg.py
│   │   │   ├── coach.py
│   │   │   ├── health.py
│   │   │   ├── food.py
│   │   │   ├── voice.py
│   │   │   ├── recommendations.py
│   │   │   ├── supplements.py
│   │   │   ├── users.py
│   │   │   ├── meals.py
│   │   │   ├── wearables.py
│   │   │   └── life_optimization.py
│   │   ├── graphql_schema.py
│   │   ├── graphql_app.py
│   │   ├── main.py          # FastAPI app
│   │   └── routes.py        # Router configuration
│   ├── database/
│   │   ├── postgres.py      # PostgreSQL connection
│   │   ├── mongo.py         # MongoDB connection
│   │   ├── base.py          # SQLAlchemy base
│   │   └── init_db.py       # Database initialization
│   ├── models/
│   │   ├── postgres_models.py
│   │   ├── mongo_schemas.py
│   │   └── life_optimization_models.py
│   └── services/
│       ├── auth_service.py
│       ├── eeg_service.py
│       ├── llm_coach_service.py
│       ├── graph_rag.py
│       ├── vector_db.py
│       ├── food_recognition.py
│       ├── voice_emotion.py
│       ├── recommendation_engine.py
│       └── [35+ service modules]
│
├── frontend/
│   ├── app.py               # Main Streamlit app
│   ├── auth_ui.py          # Authentication UI
│   └── ui_enhancements.py  # UI components
│
├── ml/
│   ├── eeg_analysis/
│   │   ├── processor.py     # EEG signal processing
│   │   ├── classifier.py    # Mental state classifier
│   │   └── features.py      # Feature extraction
│   ├── voice_emotion/
│   │   ├── analyzer.py      # Voice analysis
│   │   └── features.py      # Audio features
│   ├── food_recognition/
│   │   └── classifier.py    # Food image classification
│   └── training/
│       ├── train_eeg_model.py
│       └── train_voice_model.py
│
├── knowledge_base/
│   ├── ayurveda/
│   │   └── doshas.json
│   ├── supplements/
│   │   └── supplements_db.json
│   └── astrology/
│       └── zodiac_wellness.json
│
├── config/
│   └── settings.py          # App configuration
│
├── tests/
│   ├── test_eeg_analysis.py
│   ├── test_api_endpoints.py
│   ├── test_wellness_coach.py
│   └── [more tests]
│
├── docker/
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
│
├── kubernetes/
│   └── deployment.yaml
│
├── .env                     # Environment variables
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── GUIDE.md                 # This file
```

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_eeg_analysis.py -v

# Run with coverage
pytest tests/ -v --cov=backend --cov=ml --cov-report=html

# Run tests in parallel (faster)
pytest tests/ -v -n auto

# Run only unit tests
pytest tests/ -v -m "not integration"

# Run only integration tests
pytest tests/ -v -m integration
```

### Code Quality

```bash
# Format code with black
black backend/ frontend/ ml/

# Sort imports
isort backend/ frontend/ ml/

# Lint with flake8
flake8 backend/ frontend/ ml/ --max-line-length=100

# Type checking with mypy
mypy backend/
```

### Adding New Features

#### Example: Adding a New API Endpoint

**1. Create endpoint file:**
```python
# backend/api/endpoints/new_feature.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.postgres import get_db

router = APIRouter()

@router.post("/new-feature")
async def new_feature_endpoint(
    data: dict,
    db: AsyncSession = Depends(get_db)
):
    # Your logic here
    return {"status": "success", "data": data}
```

**2. Register in routes:**
```python
# backend/api/routes.py
from backend.api.endpoints import new_feature

api_router.include_router(
    new_feature.router,
    prefix="/new-feature",
    tags=["New Feature"]
)
```

**3. Add tests:**
```python
# tests/test_new_feature.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_new_feature(client: AsyncClient):
    response = await client.post(
        "/api/v1/new-feature",
        json={"test": "data"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

---

## 🚢 Deployment

### Docker Deployment

**Build Images:**
```bash
# Backend
docker build -t wellness-backend:v1.0 -f docker/Dockerfile.backend .

# Frontend
docker build -t wellness-frontend:v1.0 -f docker/Dockerfile.frontend .

# Push to registry
docker tag wellness-backend:v1.0 your-registry/wellness-backend:v1.0
docker push your-registry/wellness-backend:v1.0
```

**Deploy with Compose:**
```bash
# Production compose file
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment

**1. Update manifests:**
```bash
# Edit kubernetes/deployment.yaml with your image registry
sed -i 's|wellness-ai/backend|your-registry/wellness-backend:v1.0|g' kubernetes/deployment.yaml
```

**2. Create secrets:**
```bash
kubectl create namespace wellness-ai

kubectl create secret generic wellness-secrets \
  --from-literal=postgres-password=<secure-password> \
  --from-literal=mongodb-password=<secure-password> \
  --from-literal=neo4j-password=<secure-password> \
  --from-literal=jwt-secret=<secure-secret> \
  --from-literal=openai-api-key=<your-key> \
  -n wellness-ai
```

**3. Deploy:**
```bash
kubectl apply -f kubernetes/deployment.yaml -n wellness-ai

# Check status
kubectl get pods -n wellness-ai
kubectl get services -n wellness-ai

# View logs
kubectl logs -f deployment/wellness-backend -n wellness-ai
```

**4. Setup ingress:**
```bash
# Install nginx ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml

# Apply ingress rules
kubectl apply -f kubernetes/ingress.yaml -n wellness-ai
```

### Cloud Providers

<details>
<summary><b>AWS Deployment</b></summary>

**Services to use:**
- **EKS** - Kubernetes cluster
- **RDS** - PostgreSQL database
- **DocumentDB** - MongoDB compatible
- **ElastiCache** - Redis
- **S3** - File storage
- **CloudWatch** - Monitoring

**Steps:**
1. Create EKS cluster
2. Setup RDS PostgreSQL instance
3. Create DocumentDB cluster
4. Setup ElastiCache Redis
5. Create S3 bucket for uploads
6. Deploy using kubectl
7. Setup ALB ingress
8. Configure CloudWatch monitoring
</details>

<details>
<summary><b>GCP Deployment</b></summary>

**Services to use:**
- **GKE** - Kubernetes cluster
- **Cloud SQL** - PostgreSQL
- **MongoDB Atlas** - MongoDB (via GCP Marketplace)
- **Memorystore** - Redis
- **Cloud Storage** - File storage
- **Cloud Monitoring** - Monitoring

**Steps:**
1. Create GKE cluster
2. Setup Cloud SQL for PostgreSQL
3. Setup MongoDB Atlas
4. Create Memorystore instance
5. Create Cloud Storage bucket
6. Deploy using kubectl
7. Setup Load Balancer
8. Configure monitoring
</details>

### Production Checklist

- [ ] Change all default passwords
- [ ] Set `DEBUG=False`
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure HTTPS/SSL certificates
- [ ] Setup firewall rules
- [ ] Configure CORS properly
- [ ] Enable rate limiting
- [ ] Setup database backups
- [ ] Configure log rotation
- [ ] Setup monitoring alerts
- [ ] Implement health checks
- [ ] Configure auto-scaling
- [ ] Setup CI/CD pipeline
- [ ] Document runbooks
- [ ] Test disaster recovery

---

## 🔧 Troubleshooting

### Common Issues

#### Issue: Port Already in Use

**Symptom:**
```
Error: Address already in use: 8000
```

**Solution:**
```bash
# Find process using port
lsof -i :8000
# or
netstat -ano | grep 8000

# Kill process
kill -9 <PID>

# Or change port in .env
BACKEND_PORT=8001
FRONTEND_PORT=8502
```

#### Issue: Database Connection Failed

**Symptom:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution:**
```bash
# Check if database is running
docker-compose ps postgres

# Check connection
psql -h localhost -U wellness_user -d wellness_db

# Restart database
docker-compose restart postgres

# Check environment variables
echo $DATABASE_URL
```

#### Issue: Docker Out of Memory

**Symptom:**
```
Container keeps restarting, or "Out of memory" in logs
```

**Solution:**
```bash
# Increase Docker memory (Docker Desktop)
# Settings → Resources → Memory → 8GB+

# Or run fewer services
docker-compose up -d postgres mongo redis backend frontend

# Check memory usage
docker stats
```

#### Issue: Import Errors

**Symptom:**
```
ModuleNotFoundError: No module named 'pydantic_settings'
```

**Solution:**
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Or specific package
pip install pydantic-settings

# Verify installation
pip list | grep pydantic
```

#### Issue: Frontend Not Loading

**Symptom:**
Blank page or connection refused

**Solution:**
```bash
# Check if frontend is running
curl http://localhost:8501

# Check logs
docker-compose logs frontend

# Restart frontend
docker-compose restart frontend

# Clear browser cache
# Try incognito mode
# Try different browser
```

#### Issue: Knowledge Base Not Loaded

**Symptom:**
AI Coach gives generic responses without citations

**Solution:**
```bash
# Reload knowledge bases
python -c "
from backend.services.vector_db import get_vector_db
from backend.services.graph_rag import get_graph_rag

# Reset and reload vector DB
vdb = get_vector_db()
vdb.reset_database()
vdb.load_knowledge_base()

# Reload knowledge graph
graph = get_graph_rag()
graph.load_knowledge_graph()

print('Knowledge bases reloaded')
"
```

### Debug Mode

Enable detailed logging:

```bash
# In .env
DEBUG=True
LOG_LEVEL=DEBUG

# Restart services
docker-compose restart backend frontend

# View logs
docker-compose logs -f backend | grep DEBUG
```

### Clean Restart

If all else fails:

```bash
# Stop everything
docker-compose down

# Remove all data (WARNING: Deletes everything)
docker-compose down -v

# Clean Docker
docker system prune -a

# Start fresh
docker-compose up -d

# Reinitialize
python backend/database/init_db.py
```

### Getting Help

- **Documentation**: Check START_HERE.md, QUICK_REFERENCE.md
- **API Docs**: http://localhost:8000/docs
- **Logs**: `docker-compose logs -f`
- **GitHub Issues**: Report bugs and issues
- **Community**: Join discussions

---

## 🎓 Advanced Topics

### Training Custom Models

#### EEG Model Training

```bash
# Prepare dataset (DEAP or SEED format)
# Place in data/eeg/

# Train model
python ml/training/train_eeg_model.py \
  --dataset data/eeg/deap_dataset.npz \
  --epochs 100 \
  --batch-size 32 \
  --learning-rate 0.001

# Model saved to data/models/eeg_classifier.pth
# Metrics logged to MLflow
```

#### Voice Emotion Training

```bash
# Prepare RAVDESS or similar dataset
python ml/training/train_voice_model.py \
  --dataset data/audio/ravdess/ \
  --epochs 50
```

### Fine-tuning LLM Coach

```bash
# Prepare conversation dataset
python ml/training/prepare_coach_data.py

# Fine-tune with LoRA/QLoRA
python ml/training/finetune_llm.py \
  --model meta-llama/Llama-2-7b-chat-hf \
  --dataset data/coach_conversations.jsonl \
  --lora-rank 8 \
  --use-4bit
```

### Custom Knowledge Base

Add custom wellness knowledge:

**1. Create JSON file:**
```json
{
  "topic": "Custom Wellness Practice",
  "content": "Your custom wellness knowledge...",
  "evidence": ["Citation 1", "Citation 2"],
  "tags": ["tag1", "tag2"]
}
```

**2. Index in vector DB:**
```python
from backend.services.vector_db import get_vector_db

vdb = get_vector_db()
vdb.add_documents([
    {
        "content": "Your custom content",
        "metadata": {"source": "custom", "topic": "wellness"}
    }
])
```

**3. Add to knowledge graph:**
```python
from backend.services.graph_rag import get_graph_rag

graph = get_graph_rag()
graph.add_node(
    node_type="Practice",
    properties={"name": "Custom Practice", "benefits": [...]}
)
```

### API Rate Limiting

Configure in settings:

```python
# config/settings.py
RATE_LIMIT_PER_MINUTE = 60

# Apply to endpoints
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/v1/endpoint")
@limiter.limit("10/minute")
async def endpoint():
    pass
```

### Monitoring & Alerts

**Prometheus Metrics:**
```python
from prometheus_client import Counter, Histogram

api_requests = Counter('api_requests_total', 'Total API requests')
eeg_processing_time = Histogram('eeg_processing_seconds', 'EEG processing time')

@app.get("/api/v1/eeg/upload")
async def upload_eeg():
    api_requests.inc()
    with eeg_processing_time.time():
        # Process EEG
        pass
```

**Grafana Dashboards:**
- Import provided dashboards from `config/grafana/`
- Access at http://localhost:3000
- Login: admin / admin

**Setup Alerts:**
```yaml
# config/grafana/alerts.yml
groups:
  - name: wellness-ai
    interval: 1m
    rules:
      - alert: HighErrorRate
        expr: rate(api_errors_total[5m]) > 0.1
        annotations:
          summary: "High error rate detected"
```

---

## 📚 Additional Resources

### Documentation
- **START_HERE.md** - Quick orientation
- **QUICK_REFERENCE.md** - Command cheat sheet
- **COMPLETE_SETUP_GUIDE.md** - Comprehensive setup guide
- **README.md** - Project overview
- **DEPLOYMENT_GUIDE.md** - Production deployment

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **GraphQL Playground**: http://localhost:8000/graphql

### External Links
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [PyTorch Tutorials](https://pytorch.org/tutorials/)
- [LangChain Docs](https://python.langchain.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

### Community
- **GitHub Repository**: https://github.com/Srujan29112001/Wellnessapp
- **Issues**: Report bugs and feature requests
- **Discussions**: Ask questions and share ideas

---

## 🎉 Conclusion

Congratulations! You now have a complete understanding of the Wellness AI platform.

**Key Takeaways:**

- ✅ **Multi-modal health platform** combining EEG, voice, vision, and text
- ✅ **AI-powered coaching** with RAG and knowledge graphs
- ✅ **Production-ready architecture** with Docker and Kubernetes support
- ✅ **Comprehensive API** with REST and GraphQL
- ✅ **Extensible design** for custom models and knowledge

**Next Steps:**

1. Start the application
2. Explore the frontend features
3. Try the API endpoints
4. Customize for your needs
5. Deploy to production

**Happy Building! 🚀**

---

**Version:** 1.0.0
**Last Updated:** 2024-01-15
**Maintainer:** Srujan29112001
**License:** MIT

---

*For questions, issues, or contributions, visit the GitHub repository.*
