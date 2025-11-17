# 🚀 Quick Reference - Wellness AI

## ⚡ Fastest Start (Docker)

```bash
cd Wellnessapp
docker-compose up -d
python backend/database/init_db.py
```

**Access**: http://localhost:8501

---

## 🔧 Development Commands

### Start Services

```bash
# Backend API
uvicorn backend.api.main:app --reload --port 8000

# Frontend UI
streamlit run frontend/app.py --server.port 8501

# MLflow
mlflow ui --port 5000
```

### Docker Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f backend

# Restart service
docker-compose restart backend

# Rebuild
docker-compose build backend
docker-compose up -d backend
```

---

## 🗄️ Database Commands

### PostgreSQL

```bash
# Connect to database
docker-compose exec postgres psql -U wellness_user -d wellness_db

# Or locally
psql -U wellness_user -d wellness_db

# Initialize
python backend/database/init_db.py
```

### MongoDB

```bash
# Connect to MongoDB
docker-compose exec mongo mongosh -u wellness_user -p wellness_password

# Or locally
mongosh mongodb://wellness_user:wellness_password@localhost:27017
```

### Neo4j

```bash
# Access Neo4j Browser
open http://localhost:7474

# Login: neo4j / wellness_password
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_eeg_analysis.py -v

# With coverage
pytest tests/ -v --cov=backend --cov=ml
```

---

## 📡 API Testing

### Quick Health Check

```bash
curl http://localhost:8000/health
```

### Chat with AI Coach

```bash
curl -X POST "http://localhost:8000/api/v1/coach/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "I feel stressed", "user_id": "demo_user"}'
```

### Get Recommendations

```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/generate" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo_user"}'
```

---

## 🐛 Troubleshooting

### Port In Use

```bash
# Find process
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Database Connection Issues

```bash
# Check if running
docker-compose ps

# Restart databases
docker-compose restart postgres mongo redis neo4j
```

### Clean Restart

```bash
# Stop and remove everything
docker-compose down -v

# Start fresh
docker-compose up -d
python backend/database/init_db.py
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f postgres
```

---

## 🌐 Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:8501 | - |
| API Docs | http://localhost:8000/docs | - |
| GraphQL | http://localhost:8000/graphql | - |
| Neo4j Browser | http://localhost:7474 | neo4j / wellness_password |
| MLflow | http://localhost:5000 | - |
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | - |

---

## 📦 Environment Setup

### Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### Configure Environment

```bash
# .env file already created
# Edit to add API keys (optional)
nano .env

# Key settings:
OPENAI_API_KEY=sk-...        # For LLM features
ANTHROPIC_API_KEY=sk-ant-... # Alternative LLM
```

---

## 🚀 Deployment

### Build Docker Images

```bash
# Backend
docker build -t wellness-backend:latest -f docker/Dockerfile.backend .

# Frontend
docker build -t wellness-frontend:latest -f docker/Dockerfile.frontend .
```

### Deploy to Kubernetes

```bash
# Apply manifests
kubectl apply -f kubernetes/deployment.yaml -n wellness-ai

# Check status
kubectl get pods -n wellness-ai
kubectl get services -n wellness-ai
```

---

## 📊 Monitoring

### Check Service Status

```bash
# Docker
docker-compose ps

# Kubernetes
kubectl get pods -n wellness-ai

# System resources
docker stats
```

### View Metrics

```bash
# Prometheus
open http://localhost:9090

# Grafana
open http://localhost:3000
```

---

## 🔐 Security

### Change Default Passwords

Edit `.env`:
```bash
POSTGRES_PASSWORD=<secure-password>
MONGODB_PASSWORD=<secure-password>
NEO4J_PASSWORD=<secure-password>
JWT_SECRET_KEY=<secure-secret>
```

### Enable Production Mode

```bash
DEBUG=False
ENVIRONMENT=production
```

---

## 💡 Common Tasks

### Add New User

```python
python -c "
from backend.models.postgres_models import User
from backend.database.postgres import AsyncSessionLocal
import asyncio

async def create_user():
    async with AsyncSessionLocal() as session:
        user = User(
            email='user@example.com',
            name='New User',
            password_hash='hashed_password'
        )
        session.add(user)
        await session.commit()
        print(f'Created user: {user.id}')

asyncio.run(create_user())
"
```

### Reset Database

```bash
# Docker
docker-compose down -v
docker-compose up -d
python backend/database/init_db.py

# Local
dropdb wellness_db
createdb wellness_db
python backend/database/init_db.py
```

### Update Knowledge Base

```bash
# Edit knowledge_base/ayurveda/doshas.json
# Then reload

python -c "
from backend.services.graph_rag import get_graph_rag
graph = get_graph_rag()
graph.load_knowledge_graph()
print('Knowledge graph updated')
"
```

---

## 📚 Documentation

- **Complete Setup**: `COMPLETE_SETUP_GUIDE.md`
- **Quick Start**: `QUICKSTART.md`
- **Deployment**: `DEPLOYMENT_GUIDE.md`
- **Project Info**: `README.md`
- **API Docs**: http://localhost:8000/docs (when running)

---

## 🆘 Getting Help

### Check Logs

```bash
# Docker
docker-compose logs -f backend

# Local
tail -f logs/wellness_ai.log
```

### Common Issues

1. **Port in use**: Change ports in `.env`
2. **Database connection**: Check if databases are running
3. **Import errors**: Reinstall dependencies: `pip install -r requirements.txt`
4. **Out of memory**: Increase Docker memory or run fewer services

### Full Documentation

See `COMPLETE_SETUP_GUIDE.md` for detailed troubleshooting and setup instructions.

---

**Built with ❤️ for Holistic Wellness**
