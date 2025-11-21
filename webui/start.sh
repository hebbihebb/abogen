#!/bin/bash

# Abogen Web UI Launcher Script
# Starts both backend and frontend in development mode

set -e

echo "🚀 Starting Abogen Web UI..."
echo ""

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup EXIT INT TERM

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if backend dependencies are installed
if [ ! -f "$SCRIPT_DIR/backend/requirements.txt" ]; then
    echo "❌ Backend requirements.txt not found!"
    exit 1
fi

# Check if frontend dependencies are installed
if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
    echo "⚠️  Frontend dependencies not installed. Running npm install..."
    cd "$SCRIPT_DIR/frontend"
    npm install
    cd "$SCRIPT_DIR"
fi

# Start backend
echo "🔵 Starting backend server..."
cd "$SCRIPT_DIR/backend"
python main.py &
BACKEND_PID=$!
cd "$SCRIPT_DIR"

# Wait for backend to start
sleep 3

# Start frontend
echo "🟢 Starting frontend server..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"

echo ""
echo "✅ Abogen Web UI is running!"
echo ""
echo "📡 Backend API:  http://localhost:8000"
echo "🌐 Frontend UI:  http://localhost:5173"
echo "📚 API Docs:     http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
