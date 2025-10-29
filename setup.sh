#!/bin/bash
# Setup script for Exchange Rate Monitor

echo "🚀 Setting up Exchange Rate Monitor..."
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3 first: brew install python3"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

echo ""
echo "📥 Installing dependencies..."

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

echo "✅ Dependencies installed successfully"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "💡 Note: No .env file found (this is optional)"
    echo "   The script will use Frankfurter API by default (no key needed)"
    echo "   To add a backup API, create .env file:"
    echo "   cp env_template.txt .env"
    echo "   Then edit .env with your ExchangeRate-API key"
else
    echo "✅ .env file found (backup API configured)"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To run the monitor:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run the script: python exchange_rate_reminder.py"
echo ""
echo "Or run directly: ./venv/bin/python exchange_rate_reminder.py"
echo ""

