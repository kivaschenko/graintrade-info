#!/bin/bash
# Quick setup and test script for Ukrainian prices integration

echo "=================================================="
echo "Ukrainian Prices Integration Setup"
echo "=================================================="

# Check if we're in the parsers directory
if [ ! -f "yfinance_parser.py" ]; then
    echo "Error: Must be run from parsers directory"
    exit 1
fi

# Install dependencies
echo ""
echo "1. Installing dependencies..."
pip install -r requirements.txt

# Run tests
echo ""
echo "2. Running tests..."
python test_apk_parser.py

# Test daily report generation
echo ""
echo "3. Testing daily report generation..."
python yfinance_parser.py daily

echo ""
echo "=================================================="
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "  - Review fallback prices in apk_inform_parser.py"
echo "  - Update prices in get_fallback_prices() if needed"
echo "  - Configure RabbitMQ settings in .env file"
echo "  - Schedule daily and weekly reports via cron"
echo "=================================================="
