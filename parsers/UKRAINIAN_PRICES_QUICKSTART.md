# 🇺🇦 Ukrainian Prices Parser - Quick Start

## What Was Created

A comprehensive parser that fetches Ukrainian grain prices from APK-Inform and integrates them into your daily and weekly commodity reports.

## Files Added

```
parsers/
├── apk_inform_parser.py              # Main parser module
├── test_apk_parser.py                # Test suite
├── requirements.txt                  # Python dependencies
├── ukraine_prices.csv.example        # CSV template
├── setup_ukrainian_prices.sh         # Setup script
├── README_APK_INFORM.md              # Detailed documentation
└── UKRAINIAN_PRICES_IMPLEMENTATION.md # Implementation summary
```

## Quick Start

### 1. Install Dependencies

```bash
cd parsers
pip install -r requirements.txt
```

### 2. Test the Parser

```bash
python test_apk_parser.py
```

You should see: ✅ ALL TESTS PASSED

### 3. Test Daily Report with Ukrainian Prices

```bash
python yfinance_parser.py daily
```

### 4. Test Weekly Digest with Ukrainian Prices

```bash
python yfinance_parser.py weekly
```

## How It Works

The parser automatically:
1. **Tries to scrape** APK-Inform website for current prices
2. **Falls back** to approximate market prices if scraping fails
3. **Integrates** prices into daily and weekly reports
4. **Compares** Ukrainian prices with global CBOT futures

## Report Output Examples

**Daily Report:**
```
🇺🇦 Українські ціни:
• Пшениця: 8500 ₴/т (EXW)
• Кукурудза: 7200 ₴/т (EXW)
```

**Weekly Digest:**
```
🇺🇦 Українські ціни (порівняння зі світовими):
• Пшениця: 8500 ₴/т (EXW) (+10% від світової)
```

## Support

See detailed documentation in `README_APK_INFORM.md`

---

🎉 **Your Ukrainian prices parser is ready to use!**
