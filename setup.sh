#!/bin/bash

# Setup script for IBKR News Bot

echo "Setting up IBKR News Bot..."

# Find available Python
PYTHON_CMD=$(command -v python3 || command -v python)

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    echo "Activating virtual environment (Windows)..."
    source venv/Scripts/activate
else
    echo "Warning: Could not find activate script"
fi

# Install dependencies
if command -v pip &> /dev/null || command -v pip3 &> /dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt || pip3 install -r requirements.txt
else
    echo "Warning: pip not found, skipping dependency install"
    echo "You may need to run: pip install -r requirements.txt"
fi

echo ""
echo "Setup complete!"
echo "To run the bot: python ibkr_positions_news.py"
echo ""
