#!/bin/bash

# Setup script for IBKR News Bot

echo "Setting up IBKR News Bot..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo "To run the bot: python ibkr_positions_news.py"
echo ""
