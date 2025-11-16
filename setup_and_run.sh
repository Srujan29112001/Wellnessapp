#!/bin/bash

# Wellness AI - Complete Setup and Run Script
# This script sets up and runs the complete Wellness AI platform

set -e  # Exit on error

echo "=================================================="
echo "  Wellness AI - Complete Setup"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check Python
echo -e "${YELLOW}[1/7]${NC} Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3.9+."
    exit 1
fi
echo -e "${GREEN}✓${NC} Python found: $(python3 --version)"
echo ""

# Step 2: Create virtual environment
echo -e "${YELLOW}[2/7]${NC} Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment already exists"
fi
echo ""

# Step 3: Activate virtual environment and install dependencies
echo -e "${YELLOW}[3/7]${NC} Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✓${NC} Dependencies installed"
echo ""

# Step 4: Setup environment variables
echo -e "${YELLOW}[4/7]${NC} Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓${NC} Created .env file from template"
    echo "  Note: You may want to edit .env to add API keys (OpenAI, etc.)"
else
    echo -e "${GREEN}✓${NC} .env file already exists"
fi
echo ""

# Step 5: Start databases with Docker Compose
echo -e "${YELLOW}[5/7]${NC} Starting databases with Docker Compose..."
if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
    docker-compose up -d postgres mongo redis neo4j
    echo -e "${GREEN}✓${NC} Databases starting..."
    echo "  Waiting 10 seconds for databases to initialize..."
    sleep 10
else
    echo "${YELLOW}⚠${NC}  Docker not found. Please install Docker to run databases."
    echo "  Or manually configure PostgreSQL, MongoDB, Redis, and Neo4j."
fi
echo ""

# Step 6: Initialize databases
echo -e "${YELLOW}[6/7]${NC} Initializing databases and seeding data..."
python backend/database/init_db.py
echo -e "${GREEN}✓${NC} Databases initialized and seeded"
echo ""

# Step 7: Start the application
echo -e "${YELLOW}[7/7]${NC} Starting application..."
echo ""
echo "=================================================="
echo -e "${GREEN}  Setup Complete!${NC}"
echo "=================================================="
echo ""
echo "Starting services:"
echo "  • Backend API: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo "  • GraphQL: http://localhost:8000/graphql"
echo "  • Frontend: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Start backend and frontend in parallel
trap "kill 0" EXIT

# Start backend
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 &

# Start frontend
streamlit run frontend/app.py --server.port 8501 &

# Wait for all background processes
wait
