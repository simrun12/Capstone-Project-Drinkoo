#!/bin/bash
# DRINKOO Quick Start Script for Linux/macOS

echo "🥤 Starting DRINKOO Services..."
echo ""

# Check if backend is running
echo "📦 Starting Backend API..."
cd backend
uvicorn main:app --reload &
BACKEND_PID=$!

sleep 2

# Start frontend
echo "🎨 Starting Frontend Server..."
cd ..
python -m http.server 3000 --directory frontend &
FRONTEND_PID=$!

echo ""
echo "✓ DRINKOO is running!"
echo ""
echo "🔗 Open in your browser:"
echo "   http://localhost:3000"
echo ""
echo "📝 Login Credentials:"
echo "   Username: admin"
echo "   Password: password"
echo ""
echo "ℹ️  Press Ctrl+C to stop all services"
echo ""

# Keep script running
wait
