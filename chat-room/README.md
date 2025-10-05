# Chat Room Service - GrainTrade

## Overview
The Chat Room service is a real-time messaging microservice for the GrainTrade platform. Built with FastAPI and SQLAlchemy, it provides chat functionality for agricultural market participants to communicate about offers, negotiations, and general market discussions.

## Features
- 💬 **Real-time Messaging**: WebSocket-based real-time chat functionality
- 👥 **Multi-user Support**: Support for multiple users in chat rooms
- 📝 **Message Persistence**: Store chat messages in PostgreSQL database
- 🔄 **Message Queuing**: RabbitMQ integration for message processing
- ⚡ **Redis Caching**: Fast message retrieval with Redis caching
- 🔍 **Message History**: Retrieve and search through message history
- 🔐 **Authentication Integration**: Secure chat with user authentication

## Technology Stack
- **Framework**: FastAPI 0.115.12
- **Python**: 3.12+
- **Database**: PostgreSQL with async support
- **ORM**: SQLAlchemy 2.0 with async support
- **Caching**: Redis 6.4+
- **Message Broker**: RabbitMQ (aio-pika)
- **Database Migrations**: Alembic
- **Development Database**: SQLite (aiosqlite) for local development
- **ASGI Server**: Uvicorn

## Project Structure
```
chat-room/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # Database connection and configuration
│   ├── models.py            # SQLAlchemy database models
│   ├── schemas.py           # Pydantic models for request/response
│   ├── crud.py              # Database operations
│   ├── services.py          # Business logic layer
│   ├── rabbit_mq.py         # RabbitMQ configuration
│   └── redis.py             # Redis configuration
├── alembic/                 # Database migration files
├── alembic.ini             # Alembic configuration
├── Dockerfile              # Docker container configuration
├── pyproject.toml          # Poetry dependencies
├── .env                    # Environment variables (development)
└── .env.prod              # Environment variables (production)
```

## Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL (for production) or SQLite (for development)
- Redis server
- RabbitMQ server
- Poetry (for dependency management)

### 1. Environment Setup
Create environment file:
```bash
cp .env.example .env
```

Configure `.env` file:
```env
# Database
DATABASE_URL=sqlite+aiosqlite:///./chat.db
# For PostgreSQL: postgresql+asyncpg://user:password@localhost/chatdb

# Redis
REDIS_URL=redis://localhost:6379/1

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# Application
DEBUG=true
LOG_LEVEL=info
```

### 2. Install Dependencies
```bash
cd chat-room
poetry install
```

### 3. Database Setup
```bash
# Initialize Alembic (if not already done)
poetry run alembic init alembic

# Create migration
poetry run alembic revision --autogenerate -m "Create chat tables"

# Apply migrations
poetry run alembic upgrade head
```

### 4. Development Setup

#### Option A: Local Development
```bash
# Activate virtual environment
poetry shell

# Run the development server
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

#### Option B: Docker Development
```bash
# From the project root
docker-compose up chat-room --build
```

## API Documentation
Once the server is running, you can access:
- **Interactive API Documentation**: http://localhost:8001/docs
- **ReDoc Documentation**: http://localhost:8001/redoc
- **OpenAPI Schema**: http://localhost:8001/openapi.json

## Key API Endpoints

### Chat Management
- `GET /health` - Health check endpoint
- `GET /rooms/` - List available chat rooms
- `POST /rooms/` - Create a new chat room
- `GET /rooms/{room_id}` - Get room details
- `DELETE /rooms/{room_id}` - Delete a chat room

### Messages
- `GET /rooms/{room_id}/messages` - Get message history for a room
- `POST /rooms/{room_id}/messages` - Send a message to a room
- `GET /messages/{message_id}` - Get specific message details
- `DELETE /messages/{message_id}` - Delete a message

### WebSocket Endpoints
- `WS /ws/{room_id}` - WebSocket connection for real-time chat

## WebSocket Usage Example

### JavaScript Client
```javascript
// Connect to chat room
const ws = new WebSocket('ws://localhost:8001/ws/room_123');

// Send message
ws.send(JSON.stringify({
    type: 'message',
    content: 'Hello, everyone!',
    user_id: 'user_123'
}));

// Receive messages
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

### Python Client
```python
import asyncio
import websockets
import json

async def chat_client():
    uri = "ws://localhost:8001/ws/room_123"
    async with websockets.connect(uri) as websocket:
        # Send message
        await websocket.send(json.dumps({
            "type": "message",
            "content": "Hello from Python!",
            "user_id": "user_456"
        }))
        
        # Listen for messages
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")

asyncio.run(chat_client())
```

## Database Models

### Room Model
```python
class Room(Base):
    __tablename__ = "rooms"
    
    id: int (Primary Key)
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool
```

### Message Model
```python
class Message(Base):
    __tablename__ = "messages"
    
    id: int (Primary Key)
    room_id: int (Foreign Key)
    user_id: str
    content: str
    message_type: str
    created_at: datetime
    updated_at: datetime
```

## Testing
```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=app

# Run specific test file
poetry run pytest tests/test_chat.py

# Run WebSocket tests
poetry run pytest tests/test_websocket.py
```

## Deployment

### Docker Production Build
```bash
# Build the image
docker build -t graintrade-chat:latest .

# Run the container
docker run -p 8001:8001 --env-file .env.prod graintrade-chat:latest
```

### Using Docker Compose
```bash
# Production deployment
docker-compose -f docker-compose.yaml up chat-room -d
```

### Environment Variables for Production
Ensure these environment variables are set:
```env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/chatdb
REDIS_URL=redis://redis-host:6379/1
RABBITMQ_URL=amqp://user:password@rabbitmq-host:5672/
DEBUG=false
LOG_LEVEL=warning
```

## RabbitMQ Integration
The service publishes chat events to RabbitMQ for other microservices:

### Message Events
```python
# New message event
{
    "event_type": "message_created",
    "room_id": "room_123",
    "user_id": "user_456",
    "message_id": "msg_789",
    "content": "Hello!",
    "timestamp": "2024-01-01T12:00:00Z"
}

# User joined event
{
    "event_type": "user_joined",
    "room_id": "room_123",
    "user_id": "user_456",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

## Redis Caching Strategy
- **Room Data**: Cache room information for 1 hour
- **Recent Messages**: Cache last 50 messages per room for 30 minutes
- **Active Users**: Cache list of active users per room for 5 minutes
- **User Sessions**: Cache WebSocket connections for session management

## Performance Considerations
- **Message Pagination**: Implement cursor-based pagination for message history
- **WebSocket Connection Management**: Proper connection cleanup and heartbeat
- **Database Indexing**: Index on room_id, user_id, and created_at fields
- **Redis Optimization**: Use appropriate data structures (Lists, Sets, Hashes)

## Monitoring & Logging
- Health check endpoint for container orchestration
- Structured logging with correlation IDs
- WebSocket connection metrics
- Message throughput monitoring
- Error rate tracking

## Security
- WebSocket authentication via JWT tokens
- Message content validation and sanitization
- Rate limiting for message sending
- CORS configuration for WebSocket connections
- Input validation for all endpoints

## Development Guidelines

### Code Style
- Follow PEP 8 style guidelines
- Use type hints throughout the codebase
- Implement proper error handling
- Write comprehensive tests for all features

### Database Best Practices
- Use database transactions for consistency
- Implement proper migration scripts
- Index frequently queried fields
- Archive old messages periodically

### WebSocket Best Practices
- Implement connection heartbeat/ping-pong
- Handle connection drops gracefully
- Limit message size and rate
- Validate all incoming WebSocket messages

## Troubleshooting

### Common Issues
1. **WebSocket Connection Fails**
   - Check if the service is running on the correct port
   - Verify CORS settings for WebSocket connections
   - Ensure proper authentication headers

2. **Messages Not Persisting**
   - Check database connection
   - Verify database migrations are applied
   - Check application logs for errors

3. **Redis Connection Issues**
   - Verify Redis server is running
   - Check Redis URL configuration
   - Monitor Redis memory usage

## Contributing
1. Fork the repository
2. Create a feature branch
3. Implement your changes with tests
4. Ensure all tests pass
5. Submit a pull request

## License
Apache-2.0 License

## Support
For support and questions, contact: kivaschenko@protonmail.com