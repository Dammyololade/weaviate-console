#!/bin/bash

# WeactivateAdmin Run Script
# This script sets up and runs the Weaviate Admin Streamlit application

set -e  # Exit on any error

echo "🚀 Starting WeactivateAdmin..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if Streamlit secrets file exists
if [ ! -f ".streamlit/secrets.toml" ]; then
    echo "⚠️  Warning: Streamlit secrets file not found."
    echo "📝 Please copy the template: cp .streamlit/secrets.toml.template .streamlit/secrets.toml"
    echo "📝 Then edit .streamlit/secrets.toml with your configuration."
    echo "📖 For more information, see SETUP.md"
fi

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Start the Streamlit application
echo "🌐 Starting Streamlit application in watch mode..."
echo "📱 Application will be available at: http://localhost:8501"
echo "🔄 File watcher enabled - app will auto-refresh on changes"
streamlit run streamlit_app.py --server.runOnSave=true