#!/bin/bash
# Script to run the Gradio frontend

echo "Starting Warranty Agent System Frontend..."
echo "Make sure the backend API is running on http://localhost:8005"
echo ""

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "../backend/.venv" ]; then
    echo "Error: Virtual environment not found."
    echo "Please run 'cd backend && uv sync' first."
    exit 1
fi

# Activate virtual environment and run the app
source ../backend/.venv/bin/activate
python app.py
