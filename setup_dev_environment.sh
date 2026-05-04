#!/bin/bash
echo "Setting up development environment..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo "Development environment ready."
echo "To activate: source venv/bin/activate"
