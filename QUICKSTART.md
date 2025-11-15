# 🚀 Quick Start Guide - Wellness AI

This guide will help you get the Wellness AI system up and running in minutes.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.9+ (for local development)
- 8GB RAM minimum (16GB recommended)
- GPU optional (for faster ML inference)

## 🐳 Quick Start with Docker (Recommended)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd Wellnessapp

# Copy environment file
cp .env.example .env

# Edit .env with your configuration (optional for demo)
nano .env
```

### 2. Start All Services

```bash
docker-compose up -d
```

This will start:
- PostgreSQL (port 5432)
- MongoDB (port 27017)
- Redis (port 6379)
- Neo4j (port 7474, 7687)
- Backend API (port 8000)
- Frontend UI (port 8501)
- MLflow (port 5000)
- Prometheus (port 9090)
- Grafana (port 3000)

### 3. Access the Application

- **Frontend UI**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **GraphQL Playground**: http://localhost:8000/graphql
- **MLflow**: http://localhost:5000
- **Grafana Dashboards**: http://localhost:3000 (admin/admin)

### 4. Test EEG Analysis

1. Go to http://localhost:8501
2. Navigate to "🧠 EEG Analysis"
3. Upload a sample EEG CSV file (see `data/raw/sample_eeg.csv`)
4. Click "Analyze" to see mental state detection

### 5. Chat with AI Coach

1. Navigate to "💬 AI Coach"
2. Ask questions like:
   - "I feel stressed and anxious"
   - "How can I improve my sleep?"
   - "What supplements should I take for focus?"

## 💻 Local Development (Without Docker)

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Databases

You'll need to install and start PostgreSQL, MongoDB, and Redis locally, or use Docker:

```bash
# Start only databases with Docker
docker-compose up -d postgres mongo redis neo4j
```

### 3. Run Backend

```bash
# Set environment variables
export DATABASE_URL="postgresql://wellness_user:wellness_password@localhost:5432/wellness_db"
export MONGODB_URL="mongodb://localhost:27017/wellness_mongo"

# Run migrations (if applicable)
# python backend/database/migrations.py

# Start backend
uvicorn backend.api.main:app --reload --port 8000
```

### 4. Run Frontend

In a new terminal:

```bash
streamlit run frontend/app.py --server.port 8501
```

## 📊 Sample Data

Generate sample EEG data for testing:

```python
import numpy as np
import pandas as pd

# Generate 14-channel, 10-second EEG data at 256 Hz
channels = 14
duration = 10  # seconds
sample_rate = 256
samples = duration * sample_rate

# Simulate EEG with different frequency components
time = np.linspace(0, duration, samples)
eeg_data = []

for ch in range(channels):
    # Mix of frequencies (simulating alpha, beta, etc.)
    signal = (
        np.sin(2 * np.pi * 10 * time) * 0.5 +  # Alpha (10 Hz)
        np.sin(2 * np.pi * 20 * time) * 0.3 +  # Beta (20 Hz)
        np.random.randn(samples) * 0.1         # Noise
    )
    eeg_data.append(signal)

# Save to CSV
eeg_df = pd.DataFrame(eeg_data)
eeg_df.to_csv('data/raw/sample_eeg.csv', index=False, header=False)
print("Sample EEG data saved to data/raw/sample_eeg.csv")
```

## 🧪 Testing the System

### Test EEG Analysis API

```bash
curl -X POST "http://localhost:8000/api/v1/eeg/upload" \
  -F "file=@data/raw/sample_eeg.csv"
```

### Test AI Coach

```bash
curl -X POST "http://localhost:8000/api/v1/coach/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "I feel stressed and anxious"}'
```

### Test GraphQL

Visit http://localhost:8000/graphql and try:

```graphql
query {
  healthMetrics(userId: "demo_user") {
    id
    date
    steps
    stressLevel
  }
}
```

## 🔧 Troubleshooting

### Database Connection Errors

```bash
# Check if databases are running
docker-compose ps

# View logs
docker-compose logs postgres
docker-compose logs mongo

# Restart services
docker-compose restart
```

### Port Already in Use

Edit `.env` file and change ports:

```env
BACKEND_PORT=8001
FRONTEND_PORT=8502
```

### Memory Issues

If you have limited RAM, reduce services:

```bash
# Start only essential services
docker-compose up -d postgres mongo backend frontend
```

## 📚 Next Steps

1. **Customize Your Profile**
   - Go to Settings → Profile
   - Take the Ayurvedic Dosha assessment
   - Set your health goals

2. **Upload Real Data**
   - Connect EEG device (if available)
   - Log your meals and supplements
   - Track daily health metrics

3. **Explore Features**
   - Try food image recognition
   - Scan supplement labels with OCR
   - Get personalized recommendations

4. **Train Your Models**
   - See `ml/training/` for model training scripts
   - Use MLflow to track experiments
   - Fine-tune the LLM coach with your preferences

## 🛠️ Development

### Adding New Features

1. **Backend API endpoint**: Add to `backend/api/endpoints/`
2. **ML Model**: Add to `ml/<feature>/`
3. **UI Component**: Add to `frontend/app.py`
4. **Database Model**: Update `backend/models/`

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
black backend/ ml/ frontend/
flake8 backend/ ml/
```

## 📖 Documentation

- **Full Documentation**: See `docs/` folder
- **API Reference**: http://localhost:8000/docs
- **Architecture**: See `docs/ARCHITECTURE.md`
- **Contributing**: See `docs/CONTRIBUTING.md`

## ⚠️ Important Notes

- **Privacy**: All health data is encrypted at rest
- **Disclaimer**: This is a research/educational project, not medical advice
- **Consultation**: Always consult healthcare professionals for medical decisions

## 🤝 Support

- GitHub Issues: [Report bugs or request features]
- Documentation: [Link to full docs]
- Email: support@example.com

---

**Happy wellness tracking! 🧘✨**
