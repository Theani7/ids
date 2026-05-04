#!/bin/bash

# NetGuard IDS — Universal Unix Startup Script (macOS/Linux)
echo "🚀 Starting NetGuard IDS..."

# Detect OS
OS_TYPE=$(uname)
echo "💻 OS Detected: $OS_TYPE"

# Apply local ML patches if needed (specifically for certain macOS environments)
if [ "$OS_TYPE" == "Darwin" ]; then
    if [ -d "./xgboost" ]; then
        echo "✅ Applying local XGBoost patch for macOS compatibility."
        export PYTHONPATH=$PYTHONPATH:.
    fi
fi

# 1. Start Backend (FastAPI)
echo "📡 Starting Backend (FastAPI)..."
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 2. Start Frontend (Vite)
echo "🎨 Starting Frontend (React/Vite)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✨ NetGuard is now initializing!"
echo "--------------------------------------------------"
echo "Dashboard:   http://localhost:5173"
echo "Backend API: http://localhost:8000"
echo "--------------------------------------------------"
echo "⚠️  Note: Live capture requires root privileges."
echo "If capture fails, restart with: sudo ./start.sh"
echo ""
echo "Press Ctrl+C to stop both services."

# Handle graceful shutdown
trap "echo '🛑 Stopping NetGuard...'; kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM
wait
