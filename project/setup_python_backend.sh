#!/bin/bash

# Setup script for Python backend migration
# This script creates a virtual environment and installs all required dependencies

set -e  # Exit on any error

echo "🐍 Setting up Python backend for Murder Mystery game..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    
    # Try different approaches for creating venv
    if python3 -m venv venv 2>/dev/null; then
        echo "✅ Virtual environment created successfully"
    elif python3 -m venv venv --without-pip 2>/dev/null; then
        echo "✅ Virtual environment created (downloading pip separately)"
        # Download pip manually if needed
        wget https://bootstrap.pypa.io/get-pip.py -O get-pip.py
        venv/bin/python get-pip.py
        rm get-pip.py
    else
        echo "❌ Failed to create virtual environment"
        echo "💡 Try installing python3-venv: sudo apt install python3-venv"
        echo "💡 Or use system packages: pip install --break-system-packages -r requirements.txt"
        exit 1
    fi
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "📥 Installing Python dependencies..."

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

echo "✅ All dependencies installed successfully!"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Creating .env template file..."
    cat > .env << EOF
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Add your actual OpenAI API key from: https://platform.openai.com/api-keys
EOF
    echo "📝 Please update .env file with your actual OpenAI API key"
else
    echo "✅ .env file exists"
fi

echo ""
echo "🎉 Python backend setup complete!"
echo ""
echo "Next steps:"
echo "1. Update your .env file with a valid OpenAI API key"
echo "2. Test the backend: source venv/bin/activate && python backend/server.py"
echo "3. Or use npm script: npm run backend-python-dev"
echo "4. Start full app: npm run start-python"
echo ""
echo "📖 Read MIGRATION_GUIDE.md for detailed instructions"