# Quick Start Guide - YFinance Parser

## 🚀 Швидкий старт

### 1. Перевірка залежностей

```bash
cd /home/kostiantyn/projects/graintrade-info/parsers
source venv/bin/activate
pip list | grep -E "yfinance|pandas|aio_pika|requests"
```

Якщо щось відсутнє:
```bash
pip install yfinance pandas requests aio_pika python-dotenv
```

### 2. Налаштування RabbitMQ

#### Локально (для тестування):
```bash
# Запустити RabbitMQ через Docker
docker run -d --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:3-management

# Перевірити доступність
curl http://localhost:15672
# Login: guest / guest
```

#### Production (використовуйте існуючий):
Переконайтеся, що `.env` файл містить правильні налаштування:
```env
RABBITMQ_HOST=your-rabbitmq-host
RABBITMQ_PORT=5672
RABBITMQ_USER=your-user
RABBITMQ_PASS=your-password
RABBITMQ_VHOST=/
RABBITMQ_QUEUE=message.events
```

### 3. Запуск парсера

#### Щоденний звіт (для тестування):
```bash
cd /home/kostiantyn/projects/graintrade-info/parsers
venv/bin/python yfinance_parser.py daily
```

#### Тижневий дайджест:
```bash
venv/bin/python yfinance_parser.py weekly
```

### 4. Перевірка результатів

#### В консолі:
- Подивіться на попередній перегляд Telegram повідомлення
- Переконайтеся, що є повідомлення "✅ Data sent to RabbitMQ successfully!"

#### В RabbitMQ Management:
1. Відкрийте http://localhost:15672 (або ваш RabbitMQ host)
2. Перейдіть до Queues → message.events
3. Натисніть "Get messages" щоб побачити опубліковані повідомлення

#### Файл digest.md (тільки для weekly):
```bash
cat digest.md
```

### 5. Налаштування автоматичного запуску (cron)

```bash
# Редагувати crontab
crontab -e

# Додати рядки:
# Щоденний звіт о 9:00 та 18:00
0 9,18 * * * cd /home/kostiantyn/projects/graintrade-info/parsers && venv/bin/python yfinance_parser.py daily >> /tmp/yfinance_daily.log 2>&1

# Тижневий дайджест у п'ятницю о 20:00
0 20 * * 5 cd /home/kostiantyn/projects/graintrade-info/parsers && venv/bin/python yfinance_parser.py weekly >> /tmp/yfinance_weekly.log 2>&1
```

### 6. Моніторинг логів

```bash
# Для daily
tail -f /tmp/yfinance_daily.log

# Для weekly
tail -f /tmp/yfinance_weekly.log
```

## 🔧 Типові проблеми

### Проблема: "No module named 'yfinance'"
**Рішення:**
```bash
source venv/bin/activate
pip install yfinance
```

### Проблема: "Connection refused" (RabbitMQ)
**Рішення:**
1. Перевірте, що RabbitMQ запущений:
   ```bash
   docker ps | grep rabbitmq
   # або
   systemctl status rabbitmq-server
   ```
2. Перевірте налаштування в `.env`

### Проблема: Курс USD→UAH = 41.0 (fallback)
**Рішення:**
- Це нормально, якщо API недоступні
- Перевірте інтернет з'єднання
- Спробуйте пізніше (API може бути тимчасово недоступним)

### Проблема: "No data available for JO" (Coffee ETF)
**Рішення:**
- Це нормально, деякі ETF можуть бути делістовані
- Скрипт продовжить роботу з іншими тікерами
- Можете видалити Coffee ETF з COMMODITIES у yfinance_parser.py

### Проблема: Ціни виглядають занадто високими
**Рішення:**
- Перевірте, що використовуєте НОВУ версію yfinance_parser.py
- Ф'ючерси мають бути ~$5-10/bushel, не $500-1000/bushel
- Якщо все ще неправильно, перевірте `cents_per_dollar: 100` в конфігурації

## 📊 Очікувані ціни (приблизно)

**Ф'ючерси CBOT:**
- Пшениця: $4-6/bushel → 160-220 USD/т → 6500-9000 ₴/т
- Кукурудза: $3-5/bushel → 120-200 USD/т → 5000-8000 ₴/т
- Соя: $9-12/bushel → 330-440 USD/т → 13000-18000 ₴/т

**ETF:**
- WEAT: $3-5/share
- CORN: $15-20/share
- SOYB: $20-25/share

**Компанії:**
- ADM: $50-70/share
- BG: $80-110/share
- TSN: $45-60/share

## 🧪 Тестування перед production

### 1. Тест підключення
```bash
# Перевірка Yahoo Finance
venv/bin/python -c "import yfinance as yf; print(yf.Ticker('ZW=F').history(period='1d'))"

# Перевірка RabbitMQ
venv/bin/python -c "import aio_pika, asyncio; asyncio.run(aio_pika.connect_robust('amqp://guest:guest@localhost/'))"
```

### 2. Тест курсу обміну
```bash
venv/bin/python -c "
from yfinance_parser import fetch_usd_to_uah
print(f'USD/UAH: {fetch_usd_to_uah():.2f}')
"
```

### 3. Тест отримання цін
```bash
venv/bin/python -c "
from yfinance_parser import get_commodity_prices, fetch_usd_to_uah
df = get_commodity_prices(fetch_usd_to_uah())
print(df[['name', 'ticker', 'category', 'price_in_dollars']].head())
"
```

## 📝 Корисні команди

```bash
# Подивитися версію скрипта
head -20 yfinance_parser.py | grep -E "Version|Date"

# Подивитися всі тікери
grep -A 1 '"ticker":' yfinance_parser.py | grep ticker

# Підрахувати кількість commodities
grep -c '"description":' yfinance_parser.py

# Перевірити формат .env
cat .env | grep RABBITMQ

# Список останніх логів
tail -100 /tmp/yfinance_daily.log

# Очистити старі логи
> /tmp/yfinance_daily.log
> /tmp/yfinance_weekly.log
```

## 📖 Додаткова документація

- **Повна документація:** `README_YFINANCE_PARSER.md`
- **Історія змін:** `MERGE_SUMMARY.md`
- **Приклади RabbitMQ:** `sample_rabbitmq_message.json`

## 💡 Підказки

1. **Запускайте weekly тільки раз на тиждень** - це детальний звіт
2. **Daily можна запускати 2-3 рази на день** - коли відкриваються/закриваються біржі
3. **Зберігайте логи** - вони допоможуть у налагодженні
4. **Моніторте RabbitMQ черги** - переконайтеся, що повідомлення обробляються
5. **Перевіряйте курс UAH** - якщо fallback, можливо є проблеми з API

## 🎯 Готово до production?

Перевірте всі пункти:

- [ ] Залежності встановлені (`yfinance`, `pandas`, `aio_pika`, `requests`)
- [ ] RabbitMQ доступний та налаштований
- [ ] `.env` файл створений з правильними credentials
- [ ] Тестовий запуск daily пройшов успішно
- [ ] Тестовий запуск weekly пройшов успішно
- [ ] Повідомлення з'являються в RabbitMQ черзі
- [ ] Cron jobs налаштовані (опціонально)
- [ ] Логування налаштоване (опціонально)

**Якщо всі пункти виконані - готово! 🎉**

---

**Версія:** 1.0
**Дата:** 19.10.2025
