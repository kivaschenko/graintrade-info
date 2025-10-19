# Agrotender Parser - README

## Status: Beta / Fallback Mode

The Agrotender parser is currently in beta status due to the website using dynamic JavaScript rendering that requires a browser automation tool (like Selenium) to properly scrape.

## Current Implementation

### Fallback Strategy

Since Agrotender.com.ua uses dynamic content loading, the parser currently:

1. **Attempts to scrape** from the website using BeautifulSoup
2. **Falls back to APK-Inform** if scraping fails (which is currently the case)
3. **Uses static prices** as final fallback

### Why Agrotender Scraping Fails

- Website renders price tables using JavaScript
- Static HTML parsing doesn't capture dynamically loaded content
- Requires browser automation (Selenium/Playwright) to fully access data

## Future Enhancements

To make Agrotender scraping work properly, we need to:

1. **Add Selenium/Playwright** dependency for browser automation
2. **Implement headless browser** scraping
3. **Handle JavaScript rendering** wait times
4. **Extract from rendered DOM** instead of static HTML

## Current Workflow

```python
from agrotender_parser import fetch_agrotender_prices

# This will attempt Agrotender, then fall back to APK-Inform
df = fetch_agrotender_prices()
```

## Integration Status

✅ Integrated into `yfinance_parser.py`  
✅ Part of multi-source fallback chain  
⚠️  Currently falls back to APK-Inform  
❌ Agrotender scraping not working yet  

## Recommendations

For production use:

1. **Use APK-Inform parser** as primary Ukrainian source
2. **Monitor logs** to see when/if Agrotender succeeds
3. **Consider Selenium** if Agrotender-specific data is needed

## Alternative: Manual Data Entry

If real-time Agrotender data is critical:

1. Visit https://agrotender.com.ua/traders/region_ukraine
2. Manually note max prices
3. Update `ukraine_prices.csv` file
4. Parser will use CSV as fallback

## Technical Details

### What Works
- ✅ URL construction
- ✅ HTTP requests
- ✅ HTML parsing structure
- ✅ Price parsing logic
- ✅ Data structure formatting

### What Needs Work
- ❌ Dynamic content extraction
- ❌ JavaScript rendering
- ❌ Table data scraping

## License

Part of graintrade-info project.
