#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements if requirements.txt exists
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# Read API key from .env file
if [ -f ".env" ]; then
    API_KEY=$(grep API_KEY .env | cut -d '=' -f2)
    export DEEPSEEK_API_KEY=$API_KEY
    # Run the initializer with API key
    python aider-mod.py --model r1 --api-key "$API_KEY"
else
    echo "Error: .env file not found"
    exit 1
fi

# Deactivate virtual environment
deactivate 