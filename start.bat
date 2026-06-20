@echo off
REM DRINKOO Quick Start Script for Windows

echo.
echo === 🥤 DRINKOO Startup ===
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python or use the .venv environment.
    pause
    exit /b 1
)

REM Start Backend API
echo 📦 Starting Backend API on http://localhost:8000...
start "DRINKOO Backend" cmd /k "cd backend && uvicorn main:app --reload"

REM Wait a moment for backend to start
timeout /t 2 /nobreak

REM Start Frontend
echo 🎨 Starting Frontend Server on http://localhost:3000...
start "DRINKOO Frontend" cmd /k "python -m http.server 3000 --directory frontend"

REM Wait a moment for frontend to start
timeout /t 2 /nobreak

echo.
echo ✓ DRINKOO is running!
echo.
echo 🔗 Open in your browser:
echo    http://localhost:3000
echo.
echo 📝 Login Credentials:
echo    Username: admin
echo    Password: password
echo.
echo ℹ️  Close the command windows to stop services
echo.

pause
