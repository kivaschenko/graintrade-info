#!/bin/bash
# Quick test script for the grain forecast pipeline

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1
source venv/bin/activate

echo "========================================="
echo "Testing Grain Forecast Pipeline"
echo "========================================="
echo ""

python -m app.services.grain_forecast_pipeline

echo ""
echo "========================================="
echo "Test completed. Check logs above."
echo "========================================="
