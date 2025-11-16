#!/bin/bash

###############################################################################
# Stop Wellness AI Platform Services
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info "Stopping Wellness AI Platform services..."

# Stop local services if running
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null; then
        kill $BACKEND_PID
        print_success "Backend stopped (PID: $BACKEND_PID)"
    fi
    rm .backend.pid
fi

if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null; then
        kill $FRONTEND_PID
        print_success "Frontend stopped (PID: $FRONTEND_PID)"
    fi
    rm .frontend.pid
fi

# Also try to stop any orphaned processes
pkill -f "uvicorn api.main:app" 2>/dev/null && print_success "Stopped any remaining backend processes"
pkill -f "streamlit run app.py" 2>/dev/null && print_success "Stopped any remaining frontend processes"

print_success "All services stopped"
