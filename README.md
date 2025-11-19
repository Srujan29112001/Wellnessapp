# 🌟 Wellness AI Platform - Holistic Health Intelligence

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.1+-EE4C2C.svg)](https://pytorch.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://www.docker.com/)

> **An advanced AI-powered holistic wellness platform that combines EEG brain signal analysis, conversational AI coaching, astrological insights, and personalized health recommendations—merging ancient wisdom (Ayurveda, Astrology) with cutting-edge modern science.**

---

## 🎯 Project Overview

Wellness AI is a **production-ready, enterprise-grade** platform that provides:

🧠 **Neural Signal Analysis** - Real-time EEG brainwave monitoring for mental state detection
🤖 **AI Wellness Coach** - LLM-powered conversational guidance with persistent memory
🌿 **Ayurvedic Integration** - Traditional dosha assessment and personalized recommendations
⭐ **Astrological Wellness** - Natal chart analysis for personalized health insights
🔬 **Multi-Modal Health Tracking** - Voice, food recognition, supplement OCR, and biomarkers
📊 **Life Optimization** - Schedule optimization, meal planning, and progress tracking
🧘 **Spiritual Wellness** - Meditation guidance, breathing exercises, and mindfulness tools

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
│  (Streamlit: Chat, Metrics Dashboard, Recommendations)      │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│               API Layer (FastAPI + GraphQL)                 │
│  - REST endpoints  - GraphQL mutations/queries              │
│  - Authentication  - Privacy enforcement                    │
└───────────┬──────────────────────────────┬──────────────────┘
            │                              │
┌───────────▼──────────────┐    ┌─────────▼──────────────────┐
│   ML Processing Layer    │    │   Knowledge & Reasoning    │
│  - EEG Analysis (ANN)    │    │  - GraphRAG               │
│  - Voice Emotion         │    │  - Wellness KB            │
│  - Food Recognition      │    │  - LLM Coach (LangChain)  │
│  - OCR (Supplements)     │    │  - Vector DB (RAG)        │
└───────────┬──────────────┘    └─────────┬──────────────────┘
            │                              │
┌───────────▼──────────────────────────────▼──────────────────┐
│                    Data Storage Layer                        │
│  - PostgreSQL (user profiles, goals, metrics)               │
│  - MongoDB (journals, raw signals, unstructured data)       │
│  - Vector DB (embeddings for RAG)                           │
└──────────────────────────────────────────────────────────────┘
```

## 🚀 Features

### 🎯 Core Capabilities

#### 1. **EEG Signal Analysis & Mental State Detection**
   - Process multi-channel brainwave signals (delta, theta, alpha, beta, gamma bands)
   - Real-time mental state classification: stress, focus, relaxation, fatigue, drowsiness
   - CNN-LSTM hybrid architecture with optional Spiking Neural Network support
   - Batch and streaming analysis modes
   - Integration with popular EEG devices (Muse, OpenBCI, etc.)

#### 2. **Conversational AI Wellness Coach**
   - LLM-powered empathetic guidance (LangChain + HuggingFace/OpenAI/Anthropic)
   - Long-term memory and user preference tracking
   - Context-aware recommendations with scientific citations
   - Proactive check-ins and personalized nudges
   - Multi-turn conversations with emotional intelligence

#### 3. **Multi-Modal Health Intelligence**
   - 🎤 **Voice Emotion Analysis** - Detect stress, anxiety, happiness from voice patterns
   - 📸 **Food Recognition** - AI-powered meal identification and nutritional analysis
   - 🏷️ **Supplement OCR** - Scan and parse supplement labels automatically
   - 💓 **Wearable Integration** - Connect with Fitbit, Apple Health, Garmin
   - 📝 **Manual Logging** - Sleep, exercise, mood, symptoms tracking

#### 4. **Holistic Knowledge Integration**
   - 🌿 **Ayurvedic System** - Dosha assessment, herbal recommendations, dietary guidelines
   - ⭐ **Astrological Wellness** - Natal chart analysis for personalized health timing
   - 🔬 **Evidence-Based Research** - Curated knowledge from PubMed and clinical studies
   - 🧘 **Spiritual Practices** - Meditation, breathwork, mindfulness techniques
   - 💊 **Supplement Database** - Comprehensive interactions and contraindications

#### 5. **Personalized Recommendations Engine**
   - Diet plans optimized for your dosha, goals, and preferences
   - Supplement recommendations with safety checks
   - Lifestyle interventions (sleep hygiene, stress management)
   - Exercise routines tailored to energy levels and goals
   - Timing optimization based on circadian rhythms and astrological insights

### ⚡ Advanced Features

#### **Life Optimization Suite**
- 📅 **Schedule Optimizer** - AI-powered daily routine planning
- 🍽️ **Meal Plan Generator** - Personalized weekly meal plans with recipes
- 🛒 **Smart Shopping Lists** - Auto-generated grocery lists from meal plans
- 📈 **Progress Tracking** - Visual dashboards for health metrics and goal achievement
- 🧬 **Correlation Analysis** - Discover patterns between lifestyle factors and health outcomes

#### **AI & Machine Learning**
- 🧠 **GraphRAG** - Complex reasoning across interconnected health knowledge domains
- 🎯 **Multi-Modal Fusion** - Combine EEG, voice, food, and wearable data for holistic insights
- 🔮 **Predictive Analytics** - Forecast health trends and potential issues
- 🧪 **Model Quantization** - Efficient LLM inference with QLoRA/LoRA fine-tuning

#### **Wellness Tools**
- 🧘‍♀️ **Guided Sessions** - Meditation, breathing exercises, yoga routines
- 🎨 **Personality Assessment** - MBTI-style health personality profiling
- 📊 **PDF Health Reports** - Professional export of progress and recommendations
- 🔐 **Privacy-First** - End-to-end encryption, local deployment options, GDPR/HIPAA ready

## 📋 Tech Stack

### Backend
- **API Framework**: FastAPI, GraphQL (Strawberry)
- **LLM & AI**: LangChain, HuggingFace Transformers, LoRA/QLoRA
- **ML Libraries**: PyTorch, scikit-learn, MNE (EEG), librosa (audio)
- **Knowledge**: Neo4j (Graph DB), ChromaDB/Pinecone (Vector DB)

### Data Processing
- **Signal Processing**: NumPy, SciPy, MNE-Python
- **Computer Vision**: torchvision, ViT-DINO, Tesseract OCR
- **Audio**: librosa, speech_recognition, pyttsx3

### Data Storage
- **Databases**: PostgreSQL, MongoDB
- **ORMs**: SQLAlchemy, Mongoengine
- **Caching**: Redis

### ML Operations
- **Experiment Tracking**: MLflow, Weights & Biases
- **Orchestration**: Apache Airflow
- **Monitoring**: Prometheus, Grafana

### Deployment
- **Containerization**: Docker, Docker Compose
- **Orchestration**: Kubernetes
- **CI/CD**: GitHub Actions

### Frontend
- **UI Framework**: Streamlit
- **Visualization**: Plotly, matplotlib

## 🛠️ Installation & Quick Start

### Prerequisites

**Required:**
- Python 3.9+ ([Download](https://www.python.org/downloads/))
- Docker & Docker Compose ([Download](https://www.docker.com/))
- Git 2.0+

**Optional:**
- CUDA-capable GPU (for faster ML inference)
- LLM API keys (OpenAI, Anthropic Claude) or local models

### 🚀 Quick Start (Recommended - Docker)

Get up and running in **5 minutes**:

```bash
# 1. Clone the repository
git clone https://github.com/Srujan29112001/Wellnessapp.git
cd Wellnessapp

# 2. Configure environment variables
cp .env.example .env
# Edit .env with your API keys and preferences

# 3. Start all services with Docker Compose
docker-compose up -d

# 4. Wait for services to be healthy (~30 seconds)
docker-compose ps

# 5. Access the application
# Frontend: http://localhost:8501
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# GraphQL: http://localhost:8000/graphql
# MLflow: http://localhost:5000
# Grafana: http://localhost:3000
```

**That's it!** 🎉 The platform is now running with all services.

### 🔧 Manual Installation (Development)

For local development without Docker:

```bash
# 1. Clone and navigate to repository
git clone https://github.com/Srujan29112001/Wellnessapp.git
cd Wellnessapp

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Configure your database URLs, API keys, etc.

# 5. Start required services (PostgreSQL, MongoDB, Redis, Neo4j)
# Option A: Use Docker for services only
docker-compose up -d postgres mongo redis neo4j

# Option B: Install and run services locally
# See DEPLOYMENT_GUIDE.md for detailed instructions

# 6. Initialize databases
python backend/database/init_db.py

# 7. Start backend API
uvicorn backend.api.main:app --reload --port 8000

# 8. In a new terminal, start frontend
streamlit run frontend/app.py --server.port 8501
```

### 📦 Automated Setup Script

Use the included setup script for even faster installation:

```bash
chmod +x setup_and_run.sh
./setup_and_run.sh
```

This script will:
- Check prerequisites
- Set up environment variables
- Start Docker services
- Initialize databases
- Launch frontend and backend

## 📊 Project Structure

```
Wellnessapp/
├── backend/                      # Backend API & Business Logic
│   ├── api/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── routes.py            # API route aggregation
│   │   ├── graphql_app.py       # GraphQL server
│   │   └── endpoints/           # REST API endpoints
│   │       ├── auth.py          # Authentication & authorization
│   │       ├── eeg.py           # EEG analysis endpoints
│   │       ├── coach.py         # AI coach chat endpoints
│   │       ├── food.py          # Food recognition & nutrition
│   │       ├── voice.py         # Voice emotion analysis
│   │       ├── supplements.py   # Supplement scanning & recommendations
│   │       ├── wearables.py     # Wearable device integration
│   │       └── life_optimization.py  # Schedule & life optimization
│   ├── models/
│   │   ├── postgres_models.py   # SQL models (users, goals, metrics)
│   │   ├── mongo_schemas.py     # NoSQL schemas (journals, signals)
│   │   └── life_optimization_models.py  # Optimization models
│   ├── services/                # Core business logic
│   │   ├── llm_coach.py         # LangChain-based wellness coach
│   │   ├── eeg_service.py       # EEG processing service
│   │   ├── voice_service.py     # Voice emotion analysis
│   │   ├── food_recognition.py  # Food image classification
│   │   ├── ocr_service.py       # Supplement label OCR
│   │   ├── graph_rag.py         # GraphRAG knowledge reasoning
│   │   ├── recommendation_engine.py  # Personalization engine
│   │   ├── astro_wellness_service.py # Astrological insights
│   │   ├── natal_chart_service.py    # Natal chart calculations
│   │   ├── spiritual_wellness_service.py  # Spiritual practices
│   │   ├── personality_assessment_service.py  # Personality profiling
│   │   ├── meal_plan_optimizer.py    # Meal planning AI
│   │   ├── schedule_optimizer.py     # Daily schedule optimization
│   │   ├── shopping_list_service.py  # Smart grocery lists
│   │   ├── progress_tracking_service.py  # Health progress tracking
│   │   └── pdf_export_service.py     # PDF report generation
│   └── database/
│       ├── postgres.py          # PostgreSQL connection
│       ├── mongo.py             # MongoDB connection
│       └── init_db.py           # Database initialization
├── ml/                          # Machine Learning Models
│   ├── eeg_analysis/
│   │   ├── classifier.py        # EEG state classifier (CNN-LSTM)
│   │   ├── snn_classifier.py    # Spiking Neural Network variant
│   │   ├── processor.py         # Signal preprocessing
│   │   └── train_model.py       # Training scripts
│   ├── food_recognition/
│   │   ├── recognizer.py        # Food classification model
│   │   └── food_classifier.py   # ViT-based classifier
│   ├── voice_emotion/           # Voice emotion detection
│   ├── ocr/
│   │   ├── supplement_ocr.py    # Tesseract OCR wrapper
│   │   └── enhanced_nlp_parser.py  # NLP parsing
│   └── llm_finetuning/
│       ├── train_wellness_llm.py     # LLM fine-tuning
│       └── inference_wellness_llm.py # Optimized inference
├── knowledge_base/              # Curated Wellness Knowledge
│   ├── ayurveda/
│   │   └── doshas.json          # Dosha characteristics & recommendations
│   ├── astrology/
│   │   └── zodiac_wellness.json # Astrological health insights
│   └── supplements/
│       └── supplements_db.json  # Supplement database
├── frontend/                    # Streamlit User Interface
│   ├── app.py                   # Main Streamlit app
│   ├── auth_ui.py               # Authentication UI
│   └── ui_enhancements.py       # UI components
├── data/
│   ├── sample_data/             # Sample user data
│   ├── training/                # Training datasets
│   └── models/                  # Saved model checkpoints
├── airflow/
│   └── dags/                    # Data pipeline orchestration
│       ├── ml_pipeline_dag.py   # ML training pipeline
│       ├── model_retraining_dag.py  # Auto-retraining
│       └── data_quality_dag.py  # Data quality checks
├── config/
│   └── settings.py              # Application configuration
├── docker/                      # Docker configurations
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── kubernetes/                  # K8s deployment manifests
├── grafana/
│   └── dashboards/              # Monitoring dashboards
├── tests/                       # Test suite
├── docker-compose.yml           # Multi-service orchestration
├── requirements.txt             # Python dependencies
└── setup_and_run.sh            # Automated setup script
```

## 🧪 Usage Examples

### 1. Analyze EEG Data
```python
from ml.eeg_analysis.processor import EEGProcessor

processor = EEGProcessor()
mental_state = processor.analyze_eeg("path/to/eeg_data.csv")
# Output: {"stress": 0.72, "focus": 0.45, "relaxation": 0.23, "drowsiness": 0.15}
```

### 2. Chat with AI Wellness Coach
```python
from backend.services.llm_coach import WellnessCoach

coach = WellnessCoach(user_id="user123")
response = coach.chat("I feel anxious and have low energy. What should I do?")
# AI provides personalized advice based on user history, current state, and knowledge base
```

### 3. Get Personalized Recommendations
```bash
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "user_id": "user123",
    "symptoms": ["stress", "poor_sleep", "low_energy"],
    "preferences": {"diet": "vegetarian", "dosha": "vata"}
  }'
```

### 4. Analyze Food from Image
```python
from backend.services.food_recognition import FoodRecognitionService

service = FoodRecognitionService()
result = service.analyze_food_image("path/to/meal.jpg")
# Returns: food items, nutritional info, and personalized insights
```

### 5. Get Astrological Health Insights
```python
from backend.services.natal_chart_service import NatalChartService

service = NatalChartService()
insights = service.generate_natal_chart(
    birth_date="1990-05-15",
    birth_time="14:30",
    birth_location="New York, NY"
)
# Returns: natal chart analysis with health recommendations
```

### 6. Generate Meal Plan
```python
from backend.services.meal_plan_optimizer import MealPlanOptimizer

optimizer = MealPlanOptimizer()
meal_plan = optimizer.generate_weekly_plan(
    user_id="user123",
    dietary_preferences=["vegetarian", "gluten_free"],
    calorie_target=2000,
    dosha="pitta"
)
# Returns: 7-day personalized meal plan with recipes and shopping list
```

### 7. Voice Emotion Analysis
```python
from backend.services.voice_service import VoiceEmotionService

service = VoiceEmotionService()
emotion = service.analyze_voice("path/to/audio.wav")
# Output: {"emotion": "anxious", "confidence": 0.87, "stress_level": 0.72}
```

## ✨ Unique Differentiators

What sets Wellness AI apart from other health platforms:

### 🌟 Holistic Ancient-Modern Integration
- **Ayurvedic Science**: Complete dosha assessment (Vata, Pitta, Kapha) with personalized diet, lifestyle, and herbal recommendations
- **Astrological Wellness**: Natal chart analysis to optimize health activities based on planetary influences
- **Spiritual Practices**: Curated meditation, breathwork, and mindfulness techniques

### 🧠 Advanced AI & Neuroscience
- **EEG Brain Analysis**: Real-time mental state detection using neurophysiological signals
- **Multi-Modal Fusion**: Combines brain signals, voice patterns, dietary data, and biometrics for comprehensive insights
- **GraphRAG**: Knowledge graph reasoning that connects Ayurveda, modern science, nutrition, and personal health data

### 🎯 Comprehensive Life Optimization
- **AI Schedule Optimizer**: Balances work, wellness, meals, exercise, and rest based on your energy patterns
- **Personalized Meal Planning**: Weekly meal plans optimized for your dosha, goals, dietary preferences, and schedule
- **Smart Shopping Lists**: Auto-generated grocery lists that align with your meal plans
- **Correlation Discovery**: AI identifies patterns between your lifestyle choices and health outcomes

### 🔬 Production-Ready ML Pipeline
- **Spiking Neural Networks**: Bio-inspired neural models for EEG processing
- **Model Quantization**: Efficient LLM inference with QLoRA/LoRA
- **MLOps Integration**: MLflow tracking, Airflow orchestration, automated retraining
- **Monitoring**: Prometheus metrics and Grafana dashboards for system health

## 🔐 Privacy & Security

This platform takes health data privacy seriously:

- ✅ **End-to-end encryption** for all sensitive health data
- ✅ **Consent management** system for granular data collection control
- ✅ **GDPR & HIPAA considerations** - anonymization, right to deletion, data portability
- ✅ **Local-first deployment** - run entirely on-premises for complete data control
- ✅ **Audit logging** - comprehensive tracking of all data access and modifications
- ✅ **Role-based access control** (RBAC) for multi-user environments
- ✅ **Secure authentication** with JWT tokens and password hashing

## 🧠 ML Models

### EEG Classifier
- **Architecture**: CNN + LSTM or Spiking Neural Network
- **Input**: 14-channel EEG signals (raw or spectral features)
- **Output**: Mental state probabilities (stress, focus, drowsy, relaxed)
- **Training**: Supervised on labeled EEG datasets (DEAP, SEED)

### Voice Emotion Detector
- **Architecture**: wav2vec2-based transformer
- **Input**: Audio waveform
- **Output**: Emotion labels (neutral, happy, sad, angry, anxious)

### Food Recognition
- **Architecture**: ViT-DINO fine-tuned on Food-101
- **Input**: Meal photograph
- **Output**: Food categories and estimated nutrition

## 📈 Monitoring & Observability

- **Prometheus** metrics for API performance, model inference times
- **Grafana** dashboards for system health and user wellness KPIs
- **MLflow** for experiment tracking and model versioning
- **Airflow** for scheduled retraining and data pipelines

## 📚 Documentation

For comprehensive guides, see:

- **[GUIDE.md](GUIDE.md)** - Complete platform documentation with step-by-step instructions
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Production deployment instructions (Docker, Kubernetes, cloud)
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick reference for common tasks
- **[START_HERE.md](START_HERE.md)** - Getting started guide for new users
- **API Documentation** - Visit `http://localhost:8000/docs` after starting the backend

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository** and create a feature branch
2. **Make your changes** with clear, descriptive commits
3. **Test thoroughly** - ensure all tests pass
4. **Submit a pull request** with a detailed description

**Areas we'd love help with:**
- Additional EEG device integrations
- More wellness knowledge base content (herbs, practices, research)
- UI/UX improvements for the Streamlit frontend
- Additional ML model optimizations
- Documentation improvements
- Translation/internationalization

## 📄 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) for details.

You are free to use, modify, and distribute this software for personal or commercial purposes.

## 🙏 Acknowledgments

This project builds upon amazing open-source work and research:

- **EEG Analysis**: Inspired by research from DEAP, SEED, and other emotion recognition datasets
- **Ayurvedic Knowledge**: Based on classical Ayurvedic texts (Charaka Samhita, Sushruta Samhita)
- **ML Frameworks**: PyTorch, LangChain, HuggingFace Transformers community
- **Signal Processing**: MNE-Python for neurophysiological signal analysis
- **Knowledge**: PubMed research, nutritional databases, and wellness practitioners

Special thanks to the open-source community for making projects like this possible.

## 📞 Contact & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/Srujan29112001/Wellnessapp/issues)
- **GitHub Repository**: [github.com/Srujan29112001/Wellnessapp](https://github.com/Srujan29112001/Wellnessapp)

## 🎯 Roadmap

**Planned Features:**
- [ ] Mobile app (React Native)
- [ ] Real-time EEG streaming support
- [ ] Community features (sharing insights, group challenges)
- [ ] Integration with more wearable devices
- [ ] Multi-language support
- [ ] Telemedicine integration
- [ ] Advanced genomics integration (nutrigenomics)

## ⚠️ Disclaimer

**Important**: This is a research and educational project designed to explore the intersection of AI, traditional wellness wisdom, and modern health science.

- ❌ **NOT a medical device** - This system is not FDA-approved or certified for medical diagnosis
- ❌ **NOT medical advice** - Always consult qualified healthcare professionals for medical decisions
- ❌ **NOT a substitute for professional care** - This platform complements but does not replace professional medical care
- ✅ **Educational & Research** - Designed for wellness exploration, learning, and preventive health awareness

**Use at your own risk**. The developers assume no liability for health decisions made based on this platform's recommendations.

---

<div align="center">

**Built with ❤️ for holistic wellness and preventive healthcare**

⭐ Star this repo if you find it useful! | 🍴 Fork it to make it your own!

[Get Started](#-installation--quick-start) • [Documentation](#-documentation) • [Contribute](#-contributing)

</div>
