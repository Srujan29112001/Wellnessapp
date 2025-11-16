#!/bin/bash
# Master script to start the entire Wellness AI application

echo "======================================"
echo "  Wellness AI - Holistic Health Coach"
echo "======================================"
echo ""

# Change to project directory
cd "$(dirname "$0")"

# Check if databases are running
echo "📊 Checking database services..."
if ! docker ps | grep -q postgres; then
    echo "⚠️  PostgreSQL not running. Starting with docker-compose..."
    docker-compose up -d postgres mongodb redis neo4j
    echo "Waiting for databases to initialize..."
    sleep 5
fi

# Initialize databases if needed
if [ ! -f ".db_initialized" ]; then
    echo ""
    echo "🔧 First-time setup: Initializing databases..."
    python scripts/init_db.py
    if [ $? -eq 0 ]; then
        touch .db_initialized
        echo "✅ Databases initialized successfully"
    else
        echo "❌ Database initialization failed"
        exit 1
    fi
fi

echo ""
echo "======================================"
echo "Starting application services..."
echo "======================================"
echo ""

# Start backend in background
echo "🚀 Starting backend server..."
./run_backend.sh > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to start
echo "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    sleep 1
done

# Start frontend
echo ""
echo "🎨 Starting frontend..."
./run_frontend.sh &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo ""
echo "======================================"
echo "✅ Wellness AI is now running!"
echo "======================================"
echo ""
echo "📊 Backend API:  http://localhost:8000/docs"
echo "🎨 Frontend App: http://localhost:8501"
echo "📈 Monitoring:"
echo "   - Grafana:    http://localhost:3000"
echo "   - Prometheus: http://localhost:9090"
echo "   - MLflow:     http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for interrupt
trap "echo '\n\n🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" INT
wait
