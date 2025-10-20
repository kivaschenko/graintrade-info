# Fix for Notifications Service - Commodity Prices Handler

## Проблема / Problem

**Дата:** 19.10.2025

Сервіс `notifications` отримував повідомлення з RabbitMQ, але не міг знайти `telegram_message`:

```
2025-10-19 15:50:53,477 - Received commodity price notification of type: commodity_prices_weekly
2025-10-19 15:50:53,477 - No telegram_message content found in the notification data.
```

## Причина / Root Cause

### Структура повідомлення з yfinance_parser:

```json
{
  "type": "commodity_prices_daily",
  "timestamp": "2025-10-19T16:01:53.094000",
  "data": {
    "telegram_message": "📊 *Щоденний огляд...",
    "usd_uah_rate": 41.72,
    "commodities": [...]
  },
  "destination": "telegram_channel"
}
```

### Помилковий код в consumers.py:

```python
# ❌ НЕПРАВИЛЬНО
tg_text = data.get("telegram_message", "")
```

Код намагався отримати `telegram_message` з кореневого рівня об'єкта `data`, але насправді він знаходиться всередині вкладеного словника `data["data"]`.

## Рішення / Solution

### Виправлений код:

```python
# ✅ ПРАВИЛЬНО
message_data = data.get("data", {})
tg_text = message_data.get("telegram_message", "")
```

### Файл: `/notifications/app/consumers.py`

**Рядки 74-96:**

```python
# check destination channels if needed
if (
    data.get("destination") == "telegram_channel"
    and ENABLE_TELEGRAM
    and TELEGRAM_CHANNEL_ID
):
    # Extract telegram_message from nested data structure
    message_data = data.get("data", {})
    tg_text = message_data.get("telegram_message", "")
    if tg_text:
        message = await send_telegram_message(TELEGRAM_CHANNEL_ID, tg_text)
        if message:
            logging.info(
                f"Commodity prices message sent to Telegram channel {TELEGRAM_CHANNEL_ID}"
            )
        else:
            logging.error(
                "Failed to send commodity prices message to Telegram."
            )
    else:
        logging.warning(
            "No telegram_message content found in the notification data."
        )
```

## Перевірка / Testing

### 1. Запустити yfinance_parser:

```bash
cd /home/kostiantyn/projects/graintrade-info/parsers
venv/bin/python yfinance_parser.py daily
```

### 2. Перевірити логи notifications сервісу:

**Очікуваний результат:**

```
2025-10-19 16:01:53 - Received commodity price notification of type: commodity_prices_daily
2025-10-19 16:01:53 - Commodity prices message sent to Telegram channel <CHANNEL_ID>
```

### 3. Перевірити Telegram канал:

Повідомлення має з'явитися в каналі з форматуванням:

```
📊 *Щоденний огляд аграрного ринку* — 19.10.2025
💱 Курс USD→UAH: 41.72

🌾 *Ф'ючерсні контракти (CBOT):*
• Пшениця (ф'ючерс CBOT): 5.04 USD/bushel ≈ 185.10 USD/т ≈ 7722 ₴/т
...
```

## Додаткові покращення / Additional Improvements

### Рекомендації:

1. **Додати валідацію структури повідомлення:**

```python
def validate_commodity_message(data: dict) -> bool:
    """Validate commodity price message structure"""
    if not isinstance(data, dict):
        return False
    
    if "type" not in data or "data" not in data:
        return False
    
    if data["type"] not in ["commodity_prices_daily", "commodity_prices_weekly"]:
        return False
    
    message_data = data.get("data", {})
    if "telegram_message" not in message_data:
        return False
    
    return True
```

2. **Додати логування структури для налагодження:**

```python
logging.debug(f"Message structure: {json.dumps(data, indent=2, ensure_ascii=False)}")
```

3. **Обробка помилок:**

```python
try:
    message_data = data.get("data", {})
    tg_text = message_data.get("telegram_message", "")
    
    if not tg_text:
        logging.error(f"Empty telegram_message in data: {data}")
        return
    
    # ... send message
except KeyError as e:
    logging.error(f"Missing key in message structure: {e}")
except Exception as e:
    logging.error(f"Error processing commodity price message: {e}")
```

## Сумісність / Compatibility

### Підтримувані типи повідомлень:

- ✅ `commodity_prices_daily` - щоденні звіти
- ✅ `commodity_prices_weekly` - тижневі дайджести

### Формат повідомлення:

```python
{
    "type": str,                    # Type of notification
    "timestamp": str,               # ISO format timestamp
    "data": {
        "telegram_message": str,    # Formatted Telegram message
        "usd_uah_rate": float,      # Current exchange rate
        "commodities": list,        # List of commodity data
        "ukrainian_prices": list|null  # Optional Ukrainian prices
    },
    "destination": str              # Target channel
}
```

## Changelog

### 19.10.2025 - v1.0
- ✅ Виправлено доступ до вкладеної структури `data["data"]["telegram_message"]`
- ✅ Додано коментар для пояснення змін
- ✅ Протестовано з daily та weekly звітами

## Пов'язані файли / Related Files

- `/parsers/yfinance_parser.py` - генератор повідомлень
- `/notifications/app/consumers.py` - обробник повідомлень (виправлено)
- `/notifications/app/channels/telegram_ptb.py` - відправка в Telegram

## Контакти / Support

При виникненні проблем перевірте:

1. ✅ RabbitMQ працює і доступний
2. ✅ ENABLE_TELEGRAM=true в .env
3. ✅ TELEGRAM_CHANNEL_ID налаштований
4. ✅ Telegram бот має права публікувати в каналі
5. ✅ Формат повідомлення відповідає очікуваному

---

**Статус:** ✅ Виправлено та протестовано
**Версія:** 1.0
**Дата:** 19.10.2025
