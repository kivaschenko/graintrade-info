#!/bin/bash
# Quick test of Ukrainian prices parsers

echo "=================================================="
echo "Ukrainian Prices Parsers - Quick Test"
echo "=================================================="

cd "$(dirname "$0")"

echo ""
echo "1. Testing APK-Inform parser..."
echo "--------------------------------------------------"
python3 test_apk_parser.py | tail -20

echo ""
echo ""
echo "2. Testing Agrotender parser..."
echo "--------------------------------------------------"
python3 test_agrotender.py | tail -20

echo ""
echo ""
echo "3. Testing daily report generation..."
echo "--------------------------------------------------"
python3 yfinance_parser.py daily 2>&1 | grep -A 10 "🇺🇦"

echo ""
echo "=================================================="
echo "Test complete!"
echo ""
echo "Expected results:"
echo "  - APK-Inform: Should show prices (real or fallback)"
echo "  - Agrotender: Will fall back to APK-Inform"
echo "  - Daily report: Should include Ukrainian prices"
echo "=================================================="
