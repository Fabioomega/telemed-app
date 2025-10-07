#!/bin/bash

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

source venv/bin/activate
echo "Activated virtual environment."

echo "Installing dependencies"
pip install -r requirements.txt

echo "Running uvicorn"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
