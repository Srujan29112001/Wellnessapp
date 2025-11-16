# Quick Start Guide - Wellness AI Platform

## Prerequisites

- Python 3.8+ installed
- pip or pip3
- (Optional) Docker and Docker Compose for full-stack deployment

## Option 1: Quick Start (Recommended)

The fastest way to get started:

```bash
# 1. Clone or navigate to the project directory
cd Wellnessapp

# 2. Run the automated setup script
./scripts/setup_and_start.sh
```

The script will:
- ✅ Check prerequisites
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Generate sample data
- ✅ Start backend API (http://localhost:8000)
- ✅ Start frontend UI (http://localhost:8501)

## Option 2: Manual Setup

If you prefer manual control:

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env to add your API keys (optional for demo mode)

# 4. Generate sample data
python scripts/generate_sample_data.py

# 5. Start backend
cd backend
uvicorn api.main:app --reload

# 6. In a new terminal, start frontend
cd frontend
streamlit run app.py
```

## 🎯 First Steps

### 1. Access the Applications

Once running, open your browser:

- **Frontend UI**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **API Root**: http://localhost:8000

### 2. Try the Demo Features

#### EEG Analysis
1. Go to "EEG Analysis" page in Streamlit
2. Upload a sample EEG file from `data/sample_eeg/`
3. View mental state analysis and recommendations

#### AI Wellness Coach
1. Go to "AI Coach" page
2. Type a wellness question (e.g., "I'm feeling stressed and can't sleep")
3. Get personalized recommendations

**Note**: For full LLM functionality, add API keys to `.env`:
```bash
OPENAI_API_KEY=your_key_here
# OR
ANTHROPIC_API_KEY=your_key_here
```

## 🧪 Testing

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_eeg_service.py -v
```

## 🛑 Stopping Services

```bash
./scripts/stop_services.sh
```

## 📝 For Complete Documentation

See README.md for full architecture details and feature list.
