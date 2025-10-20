# Commodity Price Parser - Improvements

## Features Added

### 1. Fixed Measurement Errors
- ✅ Corrected commodity ticker symbols to use working ETFs instead of futures contracts
- ✅ Added proper error handling for failed API calls
- ✅ Improved data validation and empty data checking

### 2. Free UAH/USD Exchange Rate Parsing
- ✅ Added multiple free API sources for USD/UAH exchange rate:
  - Primary: exchangerate-api.com (no API key required)
  - Secondary: fixer.io (free tier)
  - Tertiary: National Bank of Ukraine (NBU) official rate
- ✅ Fallback mechanism when all APIs fail
- ✅ Proper error handling and logging

### 3. Extended Grain Trading Tickers
- ✅ **Agricultural ETFs:**
  - WEAT - Teucrium Wheat Fund ETF
  - CORN - Teucrium Corn Fund ETF
  - SOYB - Teucrium Soybean Fund ETF
  - DBA - Invesco DB Agriculture Fund ETF
  - CANE - Teucrium Sugar Fund ETF
  
- ✅ **Agricultural Companies:**
  - ADM - Archer-Daniels-Midland Company
  - BG - Bunge Limited
  - TSN - Tyson Foods Inc
  - MOS - The Mosaic Company (fertilizers)

### 4. Telegram Message Formatting
- ✅ Professional message layout with categories
- ✅ Emoji indicators for different asset types
- ✅ Both USD and UAH pricing
- ✅ Real-time timestamp
- ✅ Multi-language support (Ukrainian)

### 5. RabbitMQ Integration
- ✅ Async message publishing to `message.events` queue
- ✅ Structured message format for notifications service
- ✅ Error handling and connection management
- ✅ Compatible with existing backend infrastructure

## Usage

### Basic Run
```bash
cd /home/kostiantyn/projects/graintrade-info/parsers
venv/bin/python yfinance_draft.py
```

### Environment Configuration
Copy and configure the `.env` file:
```bash
cp .env.example .env
# Edit .env with your RabbitMQ credentials
```

### Dependencies
Install with Poetry:
```bash
poetry install
```

## Message Format

The script sends the following message structure to RabbitMQ:

```json
{
  "type": "commodity_prices",
  "timestamp": "2025-10-19T12:18:20.648000",
  "data": {
    "telegram_message": "📊 **Аграрний ринок** (19.10.2025)...",
    "usd_uah_rate": 41.72,
    "commodities": [...]
  },
  "destination": "telegram_channel"
}
```

## Error Handling

- Network timeouts and API failures are gracefully handled
- Missing data points are logged but don't stop execution
- Fallback to legacy function if main function fails
- Comprehensive logging for debugging

## Real Output Example

```
📊 **Аграрний ринок** (19.10.2025)
💱 Курс USD/UAH: 41.72

🌾 **Товарні ETF:**
📈 Аграрний кошик (ETF): $26.54 (1107 ₴)
📈 Кукурудза (ETF): $17.54 (732 ₴)
📈 Соя (ETF): $21.82 (910 ₴)
📈 Цукор (ETF): $9.89 (413 ₴)
📈 Пшениця (ETF): $4.05 (169 ₴)

🏭 **Аграрні компанії:**
📈 Archer-Daniels-Midland (аграрна компанія): $63.33 (2642 ₴)
📈 Bunge Limited (аграрна компанія): $97.50 (4068 ₴)
📈 Mosaic Company (добрива): $29.32 (1223 ₴)
📈 Tyson Foods (м'ясна компанія): $52.48 (2189 ₴)

📝 *Дані отримані з фондових бірж у реальному часі*
🕐 Оновлено: 12:18
```

## Next Steps

1. **Schedule automated runs**: Set up cron job or scheduler
2. **Add more tickers**: Include international grain markets
3. **Historical data**: Add price change indicators (📈/📉)
4. **Alert system**: Add price threshold notifications
5. **Dashboard**: Create web interface for real-time monitoring