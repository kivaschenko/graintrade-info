# APK-Inform Ukrainian Prices Parser

## Overview

This parser fetches current Ukrainian grain and commodity prices from the APK-Inform website (https://www.apk-inform.com/uk/prices) and integrates them into daily and weekly commodity reports.

## Features

- **Live Price Scraping**: Attempts to fetch current prices from APK-Inform website
- **Multiple Fallback Mechanisms**: 
  1. Live web scraping from APK-Inform
  2. API endpoint detection (if available)
  3. Static fallback prices (approximate market values)
- **Comprehensive Commodity Coverage**: Wheat, corn, soybeans, sunflower, barley, oats, rapeseed
- **Price Comparison**: Compares Ukrainian prices with global futures prices
- **Multiple Basis Types**: Supports EXW, CPT, FCA, FOB, DAP, CIF pricing

## Installation

Install required dependencies:

```bash
pip install -r requirements.txt
```

Dependencies:
- `beautifulsoup4` - HTML parsing
- `lxml` - HTML parser backend
- `pandas` - Data manipulation
- `requests` - HTTP requests

## Usage

### Standalone Usage

Test the parser directly:

```bash
python apk_inform_parser.py
```

### Integration with Main Parser

The APK-Inform parser is automatically integrated into the main `yfinance_parser.py`:

```python
from apk_inform_parser import fetch_ukrainian_prices

# Fetch Ukrainian prices
df_ukr = fetch_ukrainian_prices()
```

### Data Structure

The parser returns a pandas DataFrame with the following columns:

| Column | Type | Description |
|--------|------|-------------|
| `commodity` | str | Standardized commodity name (wheat, corn, soybeans, etc.) |
| `price_uah_per_ton` | float | Price in Ukrainian hryvnia per metric ton |
| `basis` | str | Price basis (EXW, CPT, FOB, etc.) |
| `source` | str | Data source (APK-Inform or APK-Inform (оціночні дані)) |
| `date` | str | Date of price data (YYYY-MM-DD) |

### Example Output

```
commodity  price_uah_per_ton  basis               source        date
    wheat              8500    EXW          APK-Inform  2025-10-19
     corn              7200    EXW          APK-Inform  2025-10-19
soybeans             16000    EXW          APK-Inform  2025-10-19
```

## Integration with Reports

### Daily Report

Ukrainian prices are automatically included in the daily report:

```python
async def generate_daily_report():
    # Get Ukrainian prices
    df_ukr = load_ukrainian_prices()
    
    # Format with Ukrainian prices
    telegram_message = format_telegram_daily_report(df, usd_to_uah, df_ukr)
```

### Weekly Digest

Ukrainian prices are included with comparison to global prices:

```python
async def generate_weekly_digest():
    # Get Ukrainian prices
    df_ukr = load_ukrainian_prices()
    
    # Format with comparison
    telegram_message = format_telegram_weekly_digest(df, usd_to_uah, df_ukr)
```

## Price Comparison Logic

The parser compares Ukrainian prices with global CBOT futures:

1. **Finds matching commodity** in futures data
2. **Calculates percentage difference**:
   - Positive = Ukrainian price higher than global
   - Negative = Ukrainian price lower than global
3. **Displays comparison** in weekly digest

Example output:
```
• Пшениця: 8500 ₴/т (EXW) (-5% від світової)
• Кукурудза: 7200 ₴/т (EXW) (-8% від світової)
```

## Fallback Mechanism

If live scraping fails, the parser uses approximate market prices:

| Commodity | Fallback Price (₴/т) | Basis |
|-----------|---------------------|-------|
| Wheat     | 8,500               | EXW   |
| Corn      | 7,200               | EXW   |
| Soybeans  | 16,000              | EXW   |
| Sunflower | 18,000              | EXW   |
| Barley    | 7,000               | EXW   |

**Note**: Fallback prices should be updated periodically to reflect current market conditions.

## Troubleshooting

### No Prices Fetched

1. **Check website availability**: Visit https://www.apk-inform.com/uk/prices
2. **Check internet connection**: Ensure network access
3. **Check rate limiting**: APK-Inform may rate-limit requests
4. **Review logs**: Check for specific error messages

### Parsing Errors

APK-Inform website structure may change. If parsing fails:

1. Inspect the HTML structure manually
2. Update CSS selectors in `extract_prices_from_html()`
3. Check for API endpoints in browser dev tools

### Fallback Data Used

If you see "APK-Inform (оціночні дані)" in the source:
- Live scraping failed
- Fallback prices are being used
- Update fallback prices in `get_fallback_prices()`

## Development

### Adding New Commodities

Add to `COMMODITY_MAPPING` in `apk_inform_parser.py`:

```python
COMMODITY_MAPPING = {
    "нова_культура": "new_crop",  # Ukrainian name
    ...
}
```

### Updating Fallback Prices

Edit `get_fallback_prices()` method:

```python
def get_fallback_prices(self) -> pd.DataFrame:
    fallback_data = [
        {
            "commodity": "wheat",
            "price_uah_per_ton": 8500,  # Update this value
            ...
        },
    ]
```

## Logging

The parser uses Python's logging module. Set log level in your application:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

Log levels:
- `INFO`: Successful operations, data fetched
- `WARNING`: Fallback mechanisms used, parsing issues
- `ERROR`: Failed requests, critical errors
- `DEBUG`: Detailed debugging information

## Future Enhancements

- [ ] Detect and use APK-Inform API if available
- [ ] Cache prices to reduce API calls
- [ ] Historical price tracking
- [ ] Regional price variations (different Ukrainian regions)
- [ ] Quality parameters (protein content, moisture)
- [ ] Export terminal prices (FOB Black Sea ports)

## License

This parser is part of the graintrade-info project.

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify APK-Inform website is accessible
3. Review fallback prices for accuracy
4. Contact project maintainers

## References

- APK-Inform Website: https://www.apk-inform.com/uk/prices
- Ukrainian Agrarian Market: https://www.apk-inform.com/uk
