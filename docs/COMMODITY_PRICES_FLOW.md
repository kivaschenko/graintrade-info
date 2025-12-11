# Commodity Prices Message Flow

## Архітектура / Architecture

```
┌─────────────────────┐
│  yfinance_parser.py │
│   (parsers/)        │
└──────────┬──────────┘
           │
           │ 1. Fetch prices from Yahoo Finance
           │ 2. Convert & format
           │ 3. Generate Telegram message
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│                     RabbitMQ                            │
│  Queue: message.events                                  │
│                                                         │
│  Message:                                               │
│  {                                                      │
│    "type": "commodity_prices_daily",                    │
│    "timestamp": "2025-10-19T16:01:53",                  │
│    "data": {                                            │
│      "telegram_message": "📊 *Щоденний огляд...",       │
│      "usd_uah_rate": 41.72,                             │
│      "commodities": [...]                               │
│    },                                                   │
│    "destination": "telegram_channel"                    │
│  }                                                      │
└─────────────────────┬───────────────────────────────────┘
                      │
                      │ Consume messages
                      │
                      ▼
           ┌──────────────────────┐
           │  consumers.py        │
           │  (notifications/)    │
           │                      │
           │  1. Parse message    │
           │  2. Extract data     │
           │  3. Route to channel │
           └──────────┬───────────┘
                      │
                      │ if destination == "telegram_channel"
                      │
                      ▼
           ┌──────────────────────┐
           │  telegram_ptb.py     │
           │  (channels/)         │
           │                      │
           │  Send to Telegram    │
           │  Channel             │
           └──────────┬───────────┘
                      │
                      ▼
           ┌──────────────────────┐
           │  Telegram Channel    │
           │  (Your channel)      │
           │                      │
           │  📊 Display message  │
           └──────────────────────┘
```

## Типи повідомлень / Message Types

### 1. Daily Report (commodity_prices_daily)

**Коли:** Кожного дня (рекомендовано: 9:00, 18:00)

**Формат:**
```
📊 *Щоденний огляд аграрного ринку* — 19.10.2025
💱 Курс USD→UAH: 41.72

🌾 *Ф'ючерсні контракти (CBOT):*
• Пшениця: 5.04 USD/bushel ≈ 185.10 USD/т ≈ 7722 ₴/т
...

📈 *Товарні ETF:*
...

🏭 *Аграрні компанії:*
...
```

**Команда запуску:**
```bash
python yfinance_parser.py daily
```

### 2. Weekly Digest (commodity_prices_weekly)

**Коли:** Раз на тиждень (рекомендовано: п'ятниця 20:00)

**Формат:**
```
📆 *Тижневий дайджест зернового ринку* — 19.10.2025
💱 USD→UAH: 41.72

🌍 *Світові біржові котирування:*
...

🇺🇦 *Українські ціни:*
...

ℹ️ *Пояснення для трейдерів:*
...
```

**Команда запуску:**
```bash
python yfinance_parser.py weekly
```

## Структура даних / Data Structure

### RabbitMQ Message Schema

```typescript
interface CommodityPriceMessage {
  type: "commodity_prices_daily" | "commodity_prices_weekly";
  timestamp: string; // ISO 8601 format
  data: {
    telegram_message: string; // Pre-formatted Telegram text
    usd_uah_rate: number;
    commodities: Commodity[];
    ukrainian_prices?: UkrainianPrice[] | null;
  };
  destination: "telegram_channel";
}

interface Commodity {
  name: string;
  ticker: string;
  category: "futures" | "etf" | "company";
  raw_price: number | null;
  price_in_dollars: number | null;
  unit: "bushel" | "share" | "cwt";
  usd_per_ton: number | null;
  uah_per_ton: number | null;
  usd_per_share: number | null;
  uah_per_share: number | null;
  description: string; // Ukrainian description
  note: string;
}

interface UkrainianPrice {
  commodity: string;
  price_uah_per_ton: number;
  price_type: "EXW" | "FOB" | "CPT";
  source: string;
}
```

## Обробка помилок / Error Handling

### 1. Parser Level (yfinance_parser.py)

```python
try:
    # Fetch prices
    df = get_commodity_prices(usd_to_uah)
    
    if df.empty:
        logger.warning("No commodity data available")
        return
    
    # Generate message
    telegram_message = format_telegram_daily_report(df, usd_to_uah)
    
    # Publish to RabbitMQ
    await publish_to_rabbitmq(message_data)
    
except Exception as e:
    logger.error(f"Error generating report: {e}")
    raise
```

### 2. Consumer Level (consumers.py)

```python
try:
    # Parse message
    data = json.loads(msg.body.decode())
    
    # Validate structure
    message_data = data.get("data", {})
    tg_text = message_data.get("telegram_message", "")
    
    if not tg_text:
        logging.warning("No telegram_message content found")
        return
    
    # Send to Telegram
    message = await send_telegram_message(TELEGRAM_CHANNEL_ID, tg_text)
    
except json.JSONDecodeError as e:
    logging.error(f"Invalid JSON: {e}")
except Exception as e:
    logging.error(f"Error processing message: {e}")
```

### 3. Telegram Level (telegram_ptb.py)

```python
try:
    # Send message with Markdown formatting
    message = await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="Markdown"
    )
    return message
    
except telegram.error.TelegramError as e:
    logging.error(f"Telegram error: {e}")
    return None
```

## Конфігурація / Configuration

### Parser (.env in parsers/)

```env
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest
RABBITMQ_VHOST=/
RABBITMQ_QUEUE=message.events
```

### Notifications (.env in notifications/)

```env
ENABLE_TELEGRAM=true
TELEGRAM_CHANNEL_ID=-1001234567890
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest
RABBITMQ_VHOST=/
```

## Моніторинг / Monitoring

### Логи Parser

```bash
# Запуск з логуванням
python yfinance_parser.py daily 2>&1 | tee /tmp/parser_daily.log

# Перевірка логів
tail -f /tmp/parser_daily.log
```

**Успішне виконання:**
```
2025-10-19 16:01:50,295 - INFO - Running daily report mode...
2025-10-19 16:01:51,103 - INFO - USD/UAH rate from exchangerate-api.com: 41.72
2025-10-19 16:01:53,092 - INFO - Message published to RabbitMQ: commodity_prices_daily
2025-10-19 16:01:53,094 - INFO - Daily report published successfully
```

### Логи Notifications

```bash
# Запуск сервісу
docker logs -f graintrade-notifications

# або
tail -f /var/log/notifications/app.log
```

**Успішна обробка:**
```
2025-10-19 16:01:53 - INFO - Received commodity price notification of type: commodity_prices_daily
2025-10-19 16:01:53 - INFO - Commodity prices message sent to Telegram channel -1001234567890
```

### RabbitMQ Management

```bash
# Перевірка черги
curl -u guest:guest http://localhost:15672/api/queues/%2F/message.events

# Або через Web UI
# http://localhost:15672
# Login: guest / guest
```

## Розклад запуску / Scheduling

### Cron Jobs

```bash
# Редагувати crontab
crontab -e

# Додати завдання:

# Daily reports (9 AM and 6 PM)
0 9 * * * /home/kostiantyn/projects/graintrade-info/parsers/venv/bin/python /home/kostiantyn/projects/graintrade-info/parsers/yfinance_parser.py daily >> /tmp/parser_daily.log 2>&1

0 18 * * * /home/kostiantyn/projects/graintrade-info/parsers/venv/bin/python /home/kostiantyn/projects/graintrade-info/parsers/yfinance_parser.py daily >> /tmp/parser_daily.log 2>&1

# Weekly digest (Friday 8 PM)
0 20 * * 5 /home/kostiantyn/projects/graintrade-info/parsers/venv/bin/python /home/kostiantyn/projects/graintrade-info/parsers/yfinance_parser.py weekly >> /tmp/parser_weekly.log 2>&1
```

### Systemd Timer (альтернатива)

**daily-parser.service:**
```ini
[Unit]
Description=Daily Commodity Price Parser
After=network.target rabbitmq.service

[Service]
Type=oneshot
User=kostiantyn
WorkingDirectory=/home/kostiantyn/projects/graintrade-info/parsers
ExecStart=/home/kostiantyn/projects/graintrade-info/parsers/venv/bin/python yfinance_parser.py daily
StandardOutput=append:/tmp/parser_daily.log
StandardError=append:/tmp/parser_daily.log
```

**daily-parser.timer:**
```ini
[Unit]
Description=Daily Commodity Price Parser Timer

[Timer]
OnCalendar=*-*-* 09,18:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

## Тестування / Testing

### 1. Тест Parser → RabbitMQ

```bash
cd /home/kostiantyn/projects/graintrade-info/parsers
venv/bin/python yfinance_parser.py daily
```

**Очікується:**
- ✅ Лог: "Message published to RabbitMQ"
- ✅ Повідомлення з'явилося в черзі `message.events`

### 2. Тест RabbitMQ → Notifications

**Перевірити чергу:**
```bash
# Web UI
http://localhost:15672 → Queues → message.events → Get messages

# CLI
sudo rabbitmqctl list_queues name messages
```

**Перевірити логи notifications:**
```bash
docker logs graintrade-notifications | tail -20
```

**Очікується:**
- ✅ Лог: "Received commodity price notification"
- ✅ Лог: "Commodity prices message sent to Telegram"

### 3. Тест Notifications → Telegram

**Перевірити канал Telegram:**
- Відкрити канал
- Побачити нове повідомлення з цінами

## Troubleshooting

### Проблема: Message published but not consumed

**Рішення:**
1. Перевірити що notifications service запущений
2. Перевірити підключення до RabbitMQ
3. Перевірити назву черги (`message.events`)

### Проблема: "No telegram_message content found"

**Рішення:**
✅ **ВИПРАВЛЕНО** - оновлено consumers.py для доступу до `data["data"]["telegram_message"]`

### Проблема: Telegram message not sent

**Рішення:**
1. Перевірити ENABLE_TELEGRAM=true
2. Перевірити TELEGRAM_CHANNEL_ID
3. Перевірити що бот є адміністратором каналу
4. Перевірити токен бота

### Проблема: Prices are 100x too high

**Рішення:**
✅ **ВИПРАВЛЕНО** - додано конверсію cents→dollars в yfinance_parser.py

## Changelog

### 19.10.2025

- ✅ Об'єднано weekly_digest.py та yfinance_parser.py
- ✅ Виправлено ціни (cents→dollars конверсія)
- ✅ Додано обробку аномалій для рису
- ✅ Виправлено consumers.py для правильного доступу до telegram_message
- ✅ Додано документацію

---

**Версія:** 1.0
**Дата:** 19.10.2025
**Статус:** ✅ Production Ready
