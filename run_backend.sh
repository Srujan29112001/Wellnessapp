#!/bin/bash
# Start Wellness AI Backend Server

echo "🚀 Starting Wellness AI Backend..."
echo ""

# Change to project directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start the backend server
echo "Starting FastAPI server on http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "GraphQL Playground: http://localhost:8000/graphql"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
