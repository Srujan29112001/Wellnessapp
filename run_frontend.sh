#!/bin/bash
# Start Wellness AI Frontend (Streamlit)

echo "🎨 Starting Wellness AI Frontend..."
echo ""

# Change to project directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Start the frontend
echo "Starting Streamlit app on http://localhost:8501"
echo ""
echo "Make sure the backend is running on http://localhost:8000"
echo "Press Ctrl+C to stop the frontend"
echo ""

streamlit run frontend/app.py --server.port 8501
