#!/bin/bash

echo "========================================"
echo "Checkmate Backend - Local Development"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Initializing database..."
python -m app.db.init_db

echo ""
echo "Starting FastAPI server..."
echo "API will be available at http://localhost:8000"
echo "API Docs will be available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

