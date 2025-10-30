#!/bin/bash
# Quick Start Script for Darpan Labs Digital Twin UI
# Run this script to start both backend and frontend

echo "🚀 Darpan Labs Digital Twin System - Quick Start"
echo "=================================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo ""
    echo "Please create .env file with your OpenAI API key:"
    echo "  echo 'export OPENAI_API_KEY=sk-your-key' >> .env"
    echo ""
    exit 1
fi

# Load environment
source .env

# Check if API key is set
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    echo "❌ Error: OPENAI_API_KEY not configured"
    echo ""
    echo "Please set your OpenAI API key in .env file:"
    echo "  nano .env"
    echo "  # Change: export OPENAI_API_KEY=sk-your-actual-key"
    echo ""
    exit 1
fi

echo "✅ OpenAI API key found"
echo ""

# Check if ui/node_modules exists
if [ ! -d "ui/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd ui
    npm install
    cd ..
    echo "✅ Frontend dependencies installed"
    echo ""
fi

# Start backend in background
echo "🔧 Starting backend API server..."
python3 -m uvicorn src.api.service:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID, logs: backend.log)"
echo ""

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start. Check backend.log for errors."
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
done
echo ""

# Start frontend
echo "🎨 Starting frontend development server..."
cd ui
npm run dev &
FRONTEND_PID=$!
cd ..
echo "✅ Frontend started (PID: $FRONTEND_PID)"
echo ""

echo "=================================================="
echo "🎉 System is running!"
echo "=================================================="
echo ""
echo "📍 Frontend: http://localhost:5173"
echo "📍 Backend API: http://localhost:8000"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT TERM

# Wait for user to stop
wait
