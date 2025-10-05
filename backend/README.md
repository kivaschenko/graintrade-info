# Backend Service - GrainTrade API

## Overview
This is the main backend service for the GrainTrade platform - an asynchronous FastAPI application that provides the core business logic for agricultural market participants. The service handles offers, user management, geographical data, and provides a comprehensive API for the frontend application.

## Features
- 🌾 **Agricultural Market Management**: Handle offers from agricultural market participants
- 🌍 **Geographical Integration**: Location-based filtering and mapping with PostGIS
- 🔐 **Authentication & Authorization**: JWT-based authentication with secure user management
- 📊 **Subscription Management**: User subscription and usage tracking
- 💰 **Payment Integration**: Payment processing capabilities
- 🐰 **RabbitMQ Integration**: Asynchronous message processing
- 📧 **Email Notifications**: Automated email sending capabilities
- 🔄 **Redis Caching**: Performance optimization with Redis

## Technology Stack
- **Framework**: FastAPI 0.115.4
- **Python**: 3.12+
- **Database**: PostgreSQL with PostGIS extension
- **ORM**: SQLAlchemy (async)
- **Caching**: Redis
- **Message Broker**: RabbitMQ (aio-pika)
- **Authentication**: JWT (PyJWT)
- **Password Hashing**: bcrypt
- **Email**: FastAPI-Mail
- **Testing**: pytest with asyncio support
- **HTTP Client**: httpx
- **ASGI Server**: Uvicorn/Gunicorn

## Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # Database connection and configuration
│   ├── schemas.py           # Pydantic models for request/response
│   ├── logger.py            # Logging configuration
│   ├── rabbit_mq.py         # RabbitMQ configuration
│   ├── models/              # SQLAlchemy database models
│   ├── routers/             # API route handlers
│   ├── service_layer/       # Business logic layer
│   ├── payments/            # Payment processing logic
│   └── utils/               # Utility functions
├── tests/                   # Test files and configurations
├── Dockerfile              # Docker container configuration
├── pyproject.toml          # Poetry dependencies
├── gunicorn.conf.py        # Gunicorn configuration
└── sample_env              # Environment variables template
```

## Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL with PostGIS extension
- Redis server
- RabbitMQ server
- Poetry (for dependency management)

### 1. Environment Setup
Copy the sample environment file and configure it:
```bash
cp sample_env .env
```

Edit `.env` file with your configuration:
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/graintrade
POSTGRES_DB=graintrade
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password

# Redis
REDIS_URL=redis://localhost:6379

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
```

### 2. Install Dependencies
```bash
cd backend
poetry install
```

### 3. Development Setup

#### Option A: Local Development
```bash
# Activate virtual environment
poetry shell

# Run the development server
fastapi dev app/main.py
```

#### Option B: Docker Development
```bash
# From the project root
docker-compose up backend --build
```

### 4. Database Setup
```bash
# Make sure PostgreSQL is running with PostGIS extension
# Create tables (if using alembic migrations)
poetry run alembic upgrade head
```

## API Documentation
Once the server is running, you can access:
- **Interactive API Documentation**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Key API Endpoints
- `GET /health` - Health check endpoint
- `POST /auth/login` - User authentication
- `POST /auth/register` - User registration
- `GET /items/` - List agricultural items
- `POST /items/` - Create new item
- `GET /categories/` - List categories
- `GET /users/me` - Get current user profile
- `POST /subscriptions/` - Manage subscriptions

## Testing
```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=app

# Run specific test file
poetry run pytest tests/test_items.py
```

## Deployment

### Docker Production Build
```bash
# Build the image
docker build -t graintrade-backend:latest .

# Run the container
docker run -p 8000:8000 --env-file .env graintrade-backend:latest
```

### Using Docker Compose
```bash
# Production deployment
docker-compose -f docker-compose.yaml up backend -d
```

### Environment Variables for Production
Ensure these environment variables are set in production:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `RABBITMQ_URL`: RabbitMQ connection string
- `SECRET_KEY`: Strong secret key for JWT
- `MAIL_*`: Email configuration for notifications

## SQL Functions & Usage
The backend includes custom SQL functions for subscription management:

```sql
-- Increment item count for a user
SELECT increment_items_count(user_id);

-- Increment map views for a user
SELECT increment_map_views(user_id);

-- Check subscription usage
SELECT * FROM get_subscription_usage(user_id);
```

## Performance Considerations
- **Database Indexing**: Ensure proper indexes on frequently queried fields
- **Redis Caching**: Cache frequently accessed data
- **Connection Pooling**: Configure appropriate database connection pools
- **Query Optimization**: Use async queries and optimize database operations

## Azure Deployment

### Create PostgreSQL Database
```bash
# Variables
RESOURCE_GROUP="graintrade-rg"
SERVER_NAME="graintrade-postgres"
LOCATION="westeurope"
ADMIN_USER="grain_admin"
ADMIN_PASSWORD="your_secure_password"
DATABASE_NAME="graintrade"

# Create PostgreSQL flexible server
az postgres flexible-server create \
    --resource-group $RESOURCE_GROUP \
    --name $SERVER_NAME \
    --location $LOCATION \
    --admin-user $ADMIN_USER \
    --admin-password $ADMIN_PASSWORD \
    --sku-name Standard_B1ms \
    --storage-size 32 \
    --version 15

# Create database
az postgres flexible-server db create \
    --resource-group $RESOURCE_GROUP \
    --server-name $SERVER_NAME \
    --database-name $DATABASE_NAME

# Enable PostGIS extension
az postgres flexible-server parameter set \
    --resource-group $RESOURCE_GROUP \
    --server-name $SERVER_NAME \
    --name azure.extensions \
    --value postgis
```

### Deploy to Azure Container Apps
```bash
# Create resource group
az group create --location westeurope --resource-group graintrade-rg

# Create container registry
az acr create \
  --resource-group graintrade-rg \
  --name graintraderegistry \
  --sku Basic \
  --admin-enabled

# Build and push image
az acr build \
  --registry graintraderegistry \
  --resource-group graintrade-rg \
  --image graintrade-backend:latest .

# Create Container Apps environment
az containerapp env create \
  --name graintrade-env \
  --resource-group graintrade-rg \
  --location westeurope

# Deploy the application
az containerapp create \
  --name graintrade-backend \
  --resource-group graintrade-rg \
  --image graintraderegistry.azurecr.io/graintrade-backend:latest \
  --environment graintrade-env \
  --ingress external \
  --target-port 8000 \
  --registry-server graintraderegistry.azurecr.io \
  --env-vars DATABASE_URL="postgresql+asyncpg://grain_admin@graintrade-postgres:password@graintrade-postgres.postgres.database.azure.com/graintrade"
```

## Monitoring & Logging
- Application logs are configured in `logger.py`
- Health check endpoint available at `/health`
- Consider integrating with monitoring solutions (Prometheus, Grafana)

## Security
- JWT tokens for authentication
- Password hashing with bcrypt
- CORS configuration for frontend integration
- Environment variable protection for sensitive data

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License
Apache-2.0 License

## Support
For support and questions, contact: kivaschenko@protonmail.com