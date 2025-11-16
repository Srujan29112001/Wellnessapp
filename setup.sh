#!/bin/bash

echo "===================================="
echo "Wellness AI Platform - Setup Script"
echo "===================================="

# Create necessary directories
echo "Creating data directories..."
mkdir -p data/vector_store
mkdir -p data/models
mkdir -p data/uploads/eeg
mkdir -p data/uploads/audio
mkdir -p data/uploads/images
mkdir -p logs

# Set up Python virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Set up environment variables
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Initialize PostgreSQL database
echo "Initializing PostgreSQL database..."
# Note: Requires PostgreSQL to be running
# You can start with: docker-compose up -d postgres

# Initialize MongoDB
echo "Initializing MongoDB..."
# Note: Requires MongoDB to be running
# You can start with: docker-compose up -d mongodb

# Download pre-trained models (optional)
echo "Downloading pre-trained models..."
# python scripts/download_models.py

echo ""
echo "===================================="
echo "Setup Complete!"
echo "===================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Start databases: docker-compose up -d postgres mongodb redis"
echo "3. Initialize databases: python scripts/init_db.py"
echo "4. Run the application: uvicorn backend.main:app --reload"
echo "5. Access API docs at: http://localhost:8000/docs"
echo ""
