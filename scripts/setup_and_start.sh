#!/bin/bash

###############################################################################
# Wellness AI Platform - Setup and Start Script
#
# This script:
# 1. Checks prerequisites
# 2. Installs dependencies
# 3. Generates sample data
# 4. Initializes databases
# 5. Starts all services (FastAPI backend + Streamlit frontend)
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if running from project root
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

print_header "Wellness AI Platform - Setup & Start"

# Step 1: Check prerequisites
print_info "Checking prerequisites..."

command -v python3 >/dev/null 2>&1 || {
    print_error "Python 3 is required but not installed. Please install Python 3.8+"
    exit 1
}
print_success "Python 3 found"

command -v pip >/dev/null 2>&1 || command -v pip3 >/dev/null 2>&1 || {
    print_error "pip is required but not installed"
    exit 1
}
print_success "pip found"

# Optional: Check for Docker
if command -v docker >/dev/null 2>&1; then
    print_success "Docker found (optional)"
    HAS_DOCKER=true
else
    print_warning "Docker not found. Will run in local mode only."
    HAS_DOCKER=false
fi

# Step 2: Create .env file if it doesn't exist
print_info "Setting up environment configuration..."

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success "Created .env from .env.example"
        print_warning "Please edit .env to add your API keys (OpenAI, Anthropic, etc.)"
    else
        print_warning ".env.example not found. You'll need to configure environment variables manually."
    fi
else
    print_success ".env file already exists"
fi

# Step 3: Install Python dependencies
print_info "Installing Python dependencies..."

# Use pip3 if available, otherwise pip
PIP_CMD=$(command -v pip3 2>/dev/null || command -v pip)

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip -q

# Install requirements
if [ -f "requirements.txt" ]; then
    print_info "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt -q
    print_success "Dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Step 4: Generate sample data
print_info "Generating sample data..."

if [ -f "scripts/generate_sample_data.py" ]; then
    python scripts/generate_sample_data.py
    print_success "Sample data generated"
else
    print_warning "Sample data script not found, skipping..."
fi

# Step 5: Create necessary directories
print_info "Creating data directories..."

mkdir -p data/vector_store
mkdir -p data/models
mkdir -p data/uploads
mkdir -p logs

print_success "Directories created"

# Step 6: Initialize knowledge base
print_info "Initializing knowledge base..."

if [ -d "knowledge_base" ]; then
    print_success "Knowledge base found"
else
    print_warning "Knowledge base not found. Some features may be limited."
fi

# Step 7: Start services
print_header "Starting Services"

# Ask user for deployment mode
echo ""
echo "Select deployment mode:"
echo "1) Local development (FastAPI + Streamlit)"
echo "2) Docker Compose (Full stack with databases)"
echo ""
read -p "Enter choice [1-2]: " choice

case $choice in
    1)
        print_info "Starting in local development mode..."

        # Start backend in background
        print_info "Starting FastAPI backend on http://localhost:8000..."
        cd backend
        uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
        BACKEND_PID=$!
        cd ..

        # Wait a bit for backend to start
        sleep 3

        # Check if backend is running
        if ps -p $BACKEND_PID > /dev/null; then
            print_success "Backend started (PID: $BACKEND_PID)"
        else
            print_error "Backend failed to start. Check logs/backend.log"
            exit 1
        fi

        # Start frontend
        print_info "Starting Streamlit frontend on http://localhost:8501..."
        cd frontend
        streamlit run app.py > ../logs/frontend.log 2>&1 &
        FRONTEND_PID=$!
        cd ..

        sleep 3

        # Check if frontend is running
        if ps -p $FRONTEND_PID > /dev/null; then
            print_success "Frontend started (PID: $FRONTEND_PID)"
        else
            print_error "Frontend failed to start. Check logs/frontend.log"
            kill $BACKEND_PID
            exit 1
        fi

        # Save PIDs
        echo $BACKEND_PID > .backend.pid
        echo $FRONTEND_PID > .frontend.pid

        print_header "Services Started Successfully!"
        echo ""
        print_success "Backend API: http://localhost:8000"
        print_success "API Documentation: http://localhost:8000/docs"
        print_success "Frontend UI: http://localhost:8501"
        echo ""
        print_info "Logs:"
        echo "  - Backend: logs/backend.log"
        echo "  - Frontend: logs/frontend.log"
        echo ""
        print_info "To stop services, run: ./scripts/stop_services.sh"
        echo ""

        # Optionally tail logs
        read -p "Show live logs? [y/N]: " show_logs
        if [ "$show_logs" = "y" ] || [ "$show_logs" = "Y" ]; then
            tail -f logs/backend.log logs/frontend.log
        fi
        ;;

    2)
        if [ "$HAS_DOCKER" = false ]; then
            print_error "Docker is required for this option but not installed"
            exit 1
        fi

        print_info "Starting with Docker Compose..."

        docker-compose up -d

        print_success "Services started with Docker Compose"
        echo ""
        print_info "Services:"
        echo "  - Backend API: http://localhost:8000"
        echo "  - Frontend UI: http://localhost:8501"
        echo "  - PostgreSQL: localhost:5432"
        echo "  - MongoDB: localhost:27017"
        echo "  - Redis: localhost:6379"
        echo "  - Neo4j: http://localhost:7474"
        echo "  - MLflow: http://localhost:5000"
        echo "  - Prometheus: http://localhost:9090"
        echo "  - Grafana: http://localhost:3000"
        echo ""
        print_info "To stop: docker-compose down"
        print_info "To view logs: docker-compose logs -f"
        ;;

    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

print_success "Setup complete!"
