#!/bin/bash

# ApaAtlas Startup Script
# Starts both backend and frontend servers

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

echo "=========================================="
echo "  Starting ApaAtlas..."
echo "=========================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "Error: node not found"
    exit 1
fi

# Start backend server
echo ""
echo "[1/2] Starting backend server on port 8000..."
cd "$BACKEND_DIR"
python3 -m uvicorn main:app --port 8000 --host 0.0.0.0 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend server
echo "[2/2] Starting frontend server on port 3000..."
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 5

echo ""
echo "=========================================="
echo "  ApaAtlas is running!"
echo "=========================================="
echo ""
echo "  Backend API:  http://localhost:8000"
echo "  Frontend:    http://localhost:3000"
echo ""
echo "  Press Ctrl+C to stop all servers"
echo ""

# Save PIDs to file for cleanup
echo "$BACKEND_PID" > /tmp/apaatlas_backend.pid
echo "$FRONTEND_PID" > /tmp/apaatlas_frontend.pid

# Wait for Ctrl+C
trap "echo ''; echo 'Stopping servers...'; kill $(cat /tmp/apaatlas_backend.pid) $(cat /tmp/apaatlas_frontend.pid) 2>/dev/null; rm -f /tmp/apaatlas_backend.pid /tmp/apaatlas_frontend.pid; exit 0" SIGINT SIGTERM

# Keep script running
wait
