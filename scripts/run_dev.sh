#!/bin/bash
# Development run script for AutoBuilder Bot

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔧 Running AutoBuilder Bot in development mode..."
echo "📁 Project directory: $PROJECT_DIR"

# Check if virtual environment exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "📦 Creating virtual environment..."
    python3.12 -m venv "$PROJECT_DIR/venv"
fi

# Activate virtual environment
source "$PROJECT_DIR/venv/bin/activate"

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip setuptools wheel
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    pip install -r "$PROJECT_DIR/requirements.txt"
else
    pip install python-telegram-bot requests psutil tomli
fi

# Create necessary directories
mkdir -p "$PROJECT_DIR/storage"
mkdir -p "$PROJECT_DIR/reports"
mkdir -p "$PROJECT_DIR/workspaces"
mkdir -p "$PROJECT_DIR/logs"

# Check if config exists
if [ ! -f "$PROJECT_DIR/config/config.toml" ]; then
    if [ -f "$PROJECT_DIR/config/config.example.toml" ]; then
        cp "$PROJECT_DIR/config/config.example.toml" "$PROJECT_DIR/config/config.toml"
        echo "⚠️  Created config.toml from example. Please edit it with your settings!"
    else
        echo "❌ Config file not found!"
        exit 1
    fi
fi

# Run the bot
echo "🚀 Starting bot..."
cd "$PROJECT_DIR"
python3 src/main.py

