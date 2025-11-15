# Personalized Wellness AI for Holistic Health

An AI-powered holistic wellness platform that combines EEG brain signal analysis, conversational AI coaching, and personalized health recommendations incorporating traditional wellness wisdom (Ayurveda) with modern science.

## 🎯 Project Overview

This project creates a comprehensive wellness coach that:
- Analyzes physiological signals (EEG brainwaves, heart rate, etc.)
- Provides personalized diet, supplement, and lifestyle recommendations
- Offers conversational AI coaching with long-term memory
- Incorporates Ayurvedic principles and modern nutritional science
- Monitors stress, focus, and mental states through biomarkers

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

### Core Capabilities
1. **EEG Signal Analysis**
   - Process brainwave signals (delta, theta, alpha, beta bands)
   - Detect mental states: stress, focus, relaxation, fatigue
   - Real-time and batch analysis support

2. **Conversational Wellness Coach**
   - LLM-powered empathetic guidance
   - Long-term memory of user preferences and history
   - Context-aware recommendations with citations
   - Proactive check-ins and nudges

3. **Multi-Modal Health Data**
   - EEG brainwaves
   - Voice emotion analysis
   - Food image recognition
   - Supplement label OCR
   - Manual input (sleep, exercise, mood)
   - Wearable data integration

4. **Holistic Knowledge Base**
   - Ayurvedic principles (doshas, herbs, practices)
   - Modern nutrition science
   - Supplement interactions and effects
   - Evidence-based wellness practices
   - Research citations from PubMed

5. **Personalized Recommendations**
   - Diet suggestions (foods, timing, portions)
   - Supplement advice with contraindications
   - Lifestyle interventions (breathing, meditation)
   - Sleep optimization
   - Stress management techniques

### Advanced Features
- GraphRAG for complex reasoning across knowledge domains
- Spiking Neural Networks (optional) for bio-inspired EEG processing
- Voice stress analysis
- Guided meditation and breathing sessions
- Adherence tracking and feedback loops
- Privacy-first design with encryption

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

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- Docker & Docker Compose
- PostgreSQL 14+
- MongoDB 5+
- CUDA-capable GPU (optional, for faster inference)

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/wellness-ai.git
cd wellness-ai
```

2. **Set up environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configurations
```

4. **Start services with Docker Compose**
```bash
docker-compose up -d
```

5. **Run database migrations**
```bash
python backend/database/migrations.py
```

6. **Start the application**
```bash
# Backend API
uvicorn backend.api.main:app --reload --port 8000

# Frontend
streamlit run frontend/app.py
```

## 📊 Project Structure

```
wellness-ai/
├── backend/
│   ├── api/              # FastAPI & GraphQL endpoints
│   ├── models/           # Database models (SQLAlchemy, Mongoengine)
│   ├── services/         # Business logic services
│   ├── database/         # Database connections & migrations
│   └── utils/            # Utility functions
├── ml/
│   ├── eeg_analysis/     # EEG signal processing & classification
│   ├── voice_emotion/    # Voice emotion detection
│   ├── food_recognition/ # Food image classification
│   └── training/         # Model training scripts
├── knowledge_base/
│   ├── ayurveda/         # Ayurvedic knowledge (doshas, herbs)
│   ├── nutrition/        # Nutrition data & research
│   └── supplements/      # Supplement database
├── frontend/             # Streamlit UI application
├── data/
│   ├── raw/              # Raw data (EEG datasets, images)
│   ├── processed/        # Processed features
│   └── models/           # Trained model checkpoints
├── config/               # Configuration files
├── docker/               # Docker configurations
├── kubernetes/           # K8s deployment manifests
├── docs/                 # Documentation
└── tests/                # Unit & integration tests
```

## 🧪 Usage Examples

### 1. Analyze EEG Data
```python
from ml.eeg_analysis.processor import EEGProcessor

processor = EEGProcessor()
mental_state = processor.analyze_eeg("path/to/eeg_data.csv")
# Output: {"stress": 0.72, "focus": 0.45, "relaxation": 0.23}
```

### 2. Chat with Wellness Coach
```python
from backend.services.coach import WellnessCoach

coach = WellnessCoach(user_id="user123")
response = coach.chat("I feel anxious and have low energy")
# AI provides personalized advice based on user history
```

### 3. Get Personalized Recommendations
```bash
curl -X POST http://localhost:8000/api/recommendations \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "symptoms": ["stress", "poor_sleep"]}'
```

## 🔐 Privacy & Security

- **End-to-end encryption** for sensitive health data
- **Consent management** for all data collection
- **GDPR/HIPAA considerations** (anonymization, right to deletion)
- **Local-first option** (run entirely on-premises)
- **Audit logging** for all data access

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

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- EEG analysis inspired by research from [Nature: EEG emotion detection](https://www.nature.com/articles/...)
- Knowledge base incorporates traditional Ayurvedic texts and modern nutritional science
- Built with love for promoting holistic wellness and preventive healthcare

## 📞 Contact

For questions or collaboration: [your-email@example.com]

---

**Disclaimer**: This is a research and educational project. Always consult qualified healthcare professionals for medical advice. This system is not a substitute for professional medical care.
