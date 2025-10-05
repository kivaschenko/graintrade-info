# Notifications Service - GrainTrade

## Overview
The Notifications service is a lightweight microservice that handles all notification delivery for the GrainTrade platform. It processes notification requests through RabbitMQ and delivers them via multiple channels including email, Telegram, and other messaging platforms. The service is designed to be efficient and reliable for handling high volumes of notifications.

## Features
- 📧 **Email Notifications**: SMTP-based email delivery with HTML templates
- 📱 **Telegram Integration**: Bot-based Telegram message delivery
- 🔄 **Multi-channel Support**: Extensible architecture for additional channels
- 🐰 **RabbitMQ Integration**: Asynchronous message processing from queue
- 📝 **Template Engine**: Jinja2-based email and message templating
- 🔐 **Secure Authentication**: JWT-based service authentication
- 📊 **Delivery Tracking**: Track notification delivery status
- 💾 **Persistent Storage**: PostgreSQL for notification history and user preferences
- ⚡ **Redis Caching**: Fast access to user preferences and templates

## Technology Stack
- **Framework**: FastAPI 0.116.1
- **Python**: 3.12+
- **Database**: PostgreSQL (async with asyncpg)
- **Template Engine**: Jinja2 3.1.6
- **Email**: aiosmtplib 4.0.1 (async SMTP)
- **Telegram**: python-telegram-bot 22.3
- **Message Broker**: RabbitMQ (aio-pika)
- **Caching**: Redis 6.2.0
- **Authentication**: PyJWT 2.10.1
- **HTTP Client**: aiohttp 3.12.15
- **ASGI Server**: Uvicorn

## Project Structure
```
notifications/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── run.py              # Application runner
│   ├── config.py           # Configuration settings
│   ├── database.py         # Database connection and configuration
│   ├── model.py            # SQLAlchemy database models
│   ├── schemas.py          # Pydantic models for request/response
│   ├── rabbit_mq.py        # RabbitMQ configuration and consumers
│   ├── consumers.py        # Message queue consumers
│   ├── channels/           # Notification delivery channels
│   │   ├── __init__.py
│   │   ├── email.py        # Email delivery implementation
│   │   ├── telegram.py     # Telegram delivery implementation
│   │   └── base.py         # Base channel interface
│   └── templates/          # Jinja2 email and message templates
├── Dockerfile              # Docker container configuration
├── pyproject.toml          # Poetry dependencies
└── README.md              # This file
```

## Notification Types

### Supported Notifications
1. **New Messages** → Notify recipient users about chat messages
2. **New Items in Category** → Notify subscribers about new agricultural offers
3. **User Registration** → Welcome emails and verification
4. **Password Reset** → Security-related notifications
5. **Subscription Reminders** → Payment and subscription updates
6. **Market Updates** → General market information

## Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL database
- Redis server
- RabbitMQ server
- SMTP server access (for email notifications)
- Telegram Bot Token (for Telegram notifications)
- Poetry (for dependency management)

### 1. Environment Setup
Create and configure environment file:
```bash
cp .env.example .env
```

Configure `.env` file:
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/notifications

# Redis
REDIS_URL=redis://localhost:6379/2

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
NOTIFICATIONS_QUEUE=notifications
NOTIFICATIONS_EXCHANGE=graintrade_notifications

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
DEFAULT_FROM_EMAIL=noreply@graintrade.info

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_WEBHOOK_URL=https://your-domain.com/telegram/webhook

# JWT Authentication
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256

# Application Settings
DEBUG=false
LOG_LEVEL=info
MAX_EMAIL_RETRIES=3
MAX_TELEGRAM_RETRIES=3
```

### 2. Install Dependencies
```bash
cd notifications
poetry install
```

### 3. Database Setup
```bash
# Create tables (if using migrations)
poetry run python -c "from app.database import create_tables; import asyncio; asyncio.run(create_tables())"
```

### 4. Development Setup

#### Option A: Local Development
```bash
# Activate virtual environment
poetry shell

# Run the service
python app/run.py

# Or using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

#### Option B: Docker Development
```bash
# From the project root
docker-compose up notifications --build
```

## API Documentation
Once the server is running, you can access:
- **Interactive API Documentation**: http://localhost:8002/docs
- **ReDoc Documentation**: http://localhost:8002/redoc
- **Health Check**: http://localhost:8002/health

## Key API Endpoints

### Service Management
- `GET /health` - Health check endpoint
- `GET /status` - Service status and metrics

### Notification Management
- `POST /notifications/send` - Send immediate notification
- `GET /notifications/{notification_id}` - Get notification details
- `GET /notifications/history` - Get notification history

### User Preferences
- `GET /users/{user_id}/preferences` - Get user notification preferences
- `PUT /users/{user_id}/preferences` - Update notification preferences
- `POST /users/{user_id}/channels/telegram` - Link Telegram account

### Telegram Webhook
- `POST /telegram/webhook` - Telegram bot webhook endpoint

## Message Queue Integration

### RabbitMQ Consumer
The service automatically consumes messages from RabbitMQ:

```python
# Example notification message format
{
    "notification_type": "new_message",
    "recipient_user_id": "user_123",
    "channels": ["email", "telegram"],
    "data": {
        "sender_name": "John Doe",
        "message_content": "Hello, I'm interested in your grain offer",
        "chat_room_id": "room_456"
    },
    "template": "new_message",
    "priority": "normal",
    "scheduled_at": null  # For immediate delivery
}
```

### Publishing Notifications
Other services can publish notifications:

```python
import aio_pika
import json

async def send_notification(notification_data):
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    channel = await connection.channel()
    
    await channel.default_exchange.publish(
        aio_pika.Message(json.dumps(notification_data).encode()),
        routing_key="notifications"
    )
    
    await connection.close()

# Example usage
await send_notification({
    "notification_type": "new_item_in_category",
    "recipient_user_id": "user_789",
    "channels": ["email"],
    "data": {
        "category_name": "Wheat",
        "item_title": "High-quality winter wheat",
        "item_location": "Kyiv region",
        "item_price": "250 USD/ton"
    },
    "template": "new_item_category"
})
```

## Notification Channels

### Email Channel
```python
# app/channels/email.py
class EmailChannel:
    async def send(self, recipient: str, subject: str, template: str, data: dict):
        # Render template
        html_content = self.render_template(template, data)
        
        # Send email
        await self.smtp_client.send_message(
            message=Message(
                subject=subject,
                recipients=[recipient],
                body=html_content,
                subtype="html"
            )
        )
```

### Telegram Channel
```python
# app/channels/telegram.py
class TelegramChannel:
    async def send(self, chat_id: str, message: str, data: dict):
        # Format message
        formatted_message = self.format_message(message, data)
        
        # Send via Telegram Bot API
        await self.bot.send_message(
            chat_id=chat_id,
            text=formatted_message,
            parse_mode="HTML"
        )
```

## Email Templates

### Template Structure
```html
<!-- templates/new_message.html -->
<!DOCTYPE html>
<html>
<head>
    <title>New Message - GrainTrade</title>
    <style>
        .container { max-width: 600px; margin: 0 auto; }
        .header { background-color: #2c5530; color: white; padding: 20px; }
        .content { padding: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>New Message from {{ sender_name }}</h1>
        </div>
        <div class="content">
            <p>You have received a new message:</p>
            <blockquote>{{ message_content }}</blockquote>
            <p>
                <a href="{{ chat_url }}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    Reply to Message
                </a>
            </p>
        </div>
    </div>
</body>
</html>
```

### Template Variables
```python
# Available template variables
{
    "user_name": "John Doe",
    "sender_name": "Jane Smith",
    "message_content": "Hello, I'm interested...",
    "item_title": "High-quality wheat",
    "category_name": "Grain",
    "price": "250 USD/ton",
    "location": "Kyiv region",
    "chat_url": "https://graintrade.info/chat/room_123",
    "unsubscribe_url": "https://graintrade.info/unsubscribe/token"
}
```

## User Preferences

### Preference Schema
```python
# User notification preferences
{
    "user_id": "user_123",
    "email_enabled": true,
    "telegram_enabled": true,
    "telegram_chat_id": "987654321",
    "preferences": {
        "new_messages": {
            "email": true,
            "telegram": false,
            "frequency": "immediate"
        },
        "new_items_category": {
            "email": true,
            "telegram": true,
            "frequency": "daily_digest"
        },
        "subscription_updates": {
            "email": true,
            "telegram": false,
            "frequency": "immediate"
        }
    },
    "quiet_hours": {
        "enabled": true,
        "start_time": "22:00",
        "end_time": "08:00",
        "timezone": "Europe/Kiev"
    }
}
```

## Testing

### Manual Testing
```bash
# Test email sending
curl -X POST "http://localhost:8002/notifications/send" \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "test",
    "recipient_user_id": "test_user",
    "channels": ["email"],
    "data": {"message": "Test notification"}
  }'
```

### Unit Testing
```bash
# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app

# Test specific channel
poetry run pytest tests/test_email_channel.py
```

## Deployment

### Docker Production Build
```bash
# Build the image
docker build -t graintrade-notifications:latest .

# Run the container
docker run -p 8002:8002 --env-file .env graintrade-notifications:latest
```

### Using Docker Compose
```bash
# Production deployment
docker-compose -f docker-compose.yaml up notifications -d
```

### Environment Variables for Production
Ensure these environment variables are properly set:
```env
DATABASE_URL=postgresql+asyncpg://user:password@prod-host:5432/notifications
REDIS_URL=redis://redis-host:6379/2
RABBITMQ_URL=amqp://user:password@rabbitmq-host:5672/
SMTP_HOST=your-smtp-server.com
SMTP_USERNAME=production-email@yourcompany.com
SMTP_PASSWORD=secure-app-password
TELEGRAM_BOT_TOKEN=production_bot_token
DEBUG=false
LOG_LEVEL=warning
```

## Monitoring & Logging

### Metrics Tracking
- **Delivery Success Rate**: Track successful notifications per channel
- **Processing Time**: Monitor queue processing performance
- **Error Rates**: Track failed deliveries and reasons
- **Queue Length**: Monitor RabbitMQ queue backlog

### Health Checks
- Database connectivity
- Redis connectivity
- RabbitMQ connectivity
- SMTP server connectivity
- Telegram Bot API connectivity

### Logging
```python
# Structured logging example
logger.info(
    "Notification sent",
    extra={
        "notification_id": notification_id,
        "user_id": user_id,
        "channel": "email",
        "delivery_time_ms": 150,
        "success": True
    }
)
```

## Security Considerations
- **Rate Limiting**: Prevent notification spam
- **Template Validation**: Sanitize template variables
- **Authentication**: Secure API endpoints with JWT
- **Data Privacy**: Handle user data according to GDPR
- **Email Security**: Implement DKIM and SPF records

## Performance Optimization
- **Batch Processing**: Group similar notifications
- **Connection Pooling**: Reuse SMTP and database connections
- **Template Caching**: Cache rendered templates
- **Async Processing**: Use async/await throughout
- **Queue Management**: Implement proper queue sizing and priority

## Troubleshooting

### Common Issues

1. **Email Delivery Failures**
   ```bash
   # Check SMTP configuration
   poetry run python -c "from app.channels.email import EmailChannel; import asyncio; asyncio.run(EmailChannel().test_connection())"
   ```

2. **Telegram Bot Issues**
   - Verify bot token validity
   - Check webhook configuration
   - Ensure bot has proper permissions

3. **RabbitMQ Connection Problems**
   - Verify RabbitMQ server is running
   - Check queue and exchange configuration
   - Monitor connection timeout settings

4. **Database Connection Issues**
   - Verify PostgreSQL connectivity
   - Check database permissions
   - Monitor connection pool usage

## Contributing
1. Fork the repository
2. Create a feature branch
3. Implement your changes with tests
4. Ensure all notifications channels work properly
5. Submit a pull request

## License
Apache-2.0 License

## Support
For support and questions, contact: kivaschenko@protonmail.com


