@echo off
echo ========================================
echo Checkmate Backend - Local Development
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Initializing database...
python -m app.db.init_db

echo.
echo Starting FastAPI server...
echo API will be available at http://localhost:8000
echo API Docs will be available at http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

