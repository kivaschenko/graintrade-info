#!/bin/bash
# Quick test script for the grain forecast pipeline

cd /home/ikost/Projects/graintrade-info/data-pipeline
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
