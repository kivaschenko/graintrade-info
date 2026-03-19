# Backend Service - GrainTrade API

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.4+-00a96e?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-blue?style=flat&logo=python)](https://python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791?style=flat&logo=postgresql)](https://postgresql.org/)

## Overview

The main backend service for the GrainTrade platform - a high-performance asynchronous FastAPI application that provides comprehensive agricultural trading functionality. This service handles user management, agricultural offers, geospatial operations, payments, and real-time communication infrastructure.

## 🚀 Features

### Core Functionality
- **🌾 Agricultural Market Management**: Complete CRUD operations for grain, seeds, fertilizers, and fuel offers
- **👥 User Management**: Registration, authentication, profiles, and subscription management
- **🗺️ Geospatial Operations**: Location-based search and filtering with PostGIS integration
- **💰 Payment Processing**: Integrated payment gateway with subscription management
- **📧 Communication**: Email notifications and messaging system

### Technical Features
- **🔐 Security**: JWT authentication, bcrypt password hashing, CORS protection
- **⚡ Performance**: Redis caching, async/await pattern, connection pooling
- **🐰 Event-Driven**: RabbitMQ integration for microservice communication
- **📊 API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **🧪 Testing**: Comprehensive test suite with pytest and asyncio
- **📈 Monitoring**: Health checks, logging, and metrics collection

## 📦 Technology Stack

### Core Framework
- **FastAPI 0.115.4+**: Modern, fast web framework with automatic API documentation
- **Python 3.12+**: Latest Python with enhanced performance and type hints
- **Uvicorn/Gunicorn**: ASGI server for production deployment

### Database & Storage
- **PostgreSQL 16+**: Primary database with ACID compliance
- **PostGIS**: Geospatial extension for location-based operations
- **SQLAlchemy 2.0**: Modern async ORM with advanced querying
- **Asyncpg**: High-performance PostgreSQL driver
- **Redis**: Caching and session storage

### Integration & Communication
- **RabbitMQ**: Message broker for service communication
- **aio-pika**: Async RabbitMQ client
- **FastAPI-Mail**: Email sending capabilities
- **httpx**: Modern HTTP client for external API calls

### Security & Authentication
- **PyJWT**: JSON Web Token implementation
- **bcrypt**: Secure password hashing
- **Pydantic**: Data validation and serialization

### Development & Testing
- **Poetry**: Modern dependency management
- **pytest**: Testing framework with async support
- **httpx**: Test client for API testing

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application and startup
│   ├── database.py          # Database configuration and connection
│   ├── schemas.py           # Pydantic models (request/response)
│   ├── logger.py            # Structured logging configuration
│   ├── rabbit_mq.py         # RabbitMQ setup and producers
│   ├── models/              # SQLAlchemy database models
│   │   ├── __init__.py
│   │   ├── user.py          # User and subscription models
│   │   ├── item.py          # Agricultural item models
│   │   └── ...              # Additional domain models
│   ├── routers/             # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── users.py         # User management
│   │   ├── items.py         # Agricultural items CRUD
│   │   ├── categories.py    # Item categories
│   │   └── ...              # Additional route modules
│   ├── service_layer/       # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py  # Authentication business logic
│   │   ├── item_service.py  # Item management logic
│   │   └── ...              # Additional service modules
│   ├── payments/            # Payment processing
│   │   ├── __init__.py
│   │   ├── providers.py     # Payment provider integrations
│   │   └── schemas.py       # Payment-related schemas
│   └── utils/               # Utility functions
│       ├── __init__.py
│       ├── security.py      # Security utilities
│       ├── dependencies.py  # FastAPI dependencies
│       └── ...              # Additional utilities
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── conftest.py         # Test configuration and fixtures
│   ├── test_auth.py        # Authentication tests
│   ├── test_items.py       # Item management tests
│   └── ...                 # Additional test modules
├── Dockerfile              # Container configuration
├── pyproject.toml          # Poetry dependencies and project config
├── gunicorn.conf.py        # Production server configuration
├── sample_env              # Environment variables template
└── README.md               # This documentation
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.12+**: Latest Python version
- **PostgreSQL 16+**: With PostGIS extension
- **Redis 7+**: For caching and sessions
- **RabbitMQ 3.12+**: Message broker
- **Poetry**: Dependency management

### 1. Environment Configuration

```bash
# Copy and configure environment
cp sample_env .env
```

Configure your `.env` file:
```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://graintrade_user:secure_password@localhost:5432/graintrade_db
POSTGRES_DB=graintrade_db
POSTGRES_USER=graintrade_user
POSTGRES_PASSWORD=secure_password

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# RabbitMQ Configuration
RABBITMQ_URL=amqp://graintrade:graintrade_pass@localhost:5672/graintrade_vhost

# Security Configuration
SECRET_KEY=your-ultra-secure-secret-key-here-64-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration
MAIL_USERNAME=noreply@graintrade.info
MAIL_PASSWORD=your-app-specific-password
MAIL_FROM=noreply@graintrade.info
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_FROM_NAME="GrainTrade Platform"

# External Services
MAPBOX_ACCESS_TOKEN=your_mapbox_token_here
PAYMENT_PROVIDER_API_KEY=your_payment_api_key

# Application Settings
DEBUG=false
CORS_ORIGINS=["https://graintrade.info", "https://www.graintrade.info"]
```

### 2. Development Setup

```bash
# Install dependencies
cd backend
poetry install

# Activate virtual environment
poetry shell

# Run development server
fastapi dev app/main.py
```

### 3. Database Setup

```bash
# Create database and user (PostgreSQL)
sudo -u postgres psql
CREATE DATABASE graintrade_db;
CREATE USER graintrade_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE graintrade_db TO graintrade_user;
CREATE EXTENSION postgis;  # Enable PostGIS
\q

# Run migrations (if using Alembic)
alembic upgrade head
```

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

### 4. Access the Application

The backend will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📖 API Documentation

### Auto-Generated Documentation
Once the server is running, you can access:
- **Swagger UI**: http://localhost:8000/docs - Interactive API testing
- **ReDoc**: http://localhost:8000/redoc - Clean documentation
- **OpenAPI Schema**: http://localhost:8000/openapi.json - Raw schema

### Core API Endpoints

#### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - User logout
- `POST /auth/forgot-password` - Password reset request

#### User Management
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update user profile
- `GET /users/me/subscription` - Get subscription details
- `POST /users/me/subscription` - Update subscription

#### Agricultural Items
- `GET /items/` - List items with filtering and pagination
- `POST /items/` - Create new agricultural item
- `GET /items/{item_id}` - Get specific item details
- `PUT /items/{item_id}` - Update item (owner only)
- `DELETE /items/{item_id}` - Delete item (owner only)
- `GET /items/search` - Advanced search with geospatial filtering

#### Categories & Data
- `GET /categories/` - List all item categories
- `GET /categories/{category_id}/items` - Items by category
- `GET /regions/` - Geographic regions
- `GET /units/` - Measurement units

#### System
- `GET /health` - Service health check
- `GET /metrics` - Application metrics (for monitoring)

## 🧪 Testing

### Running Tests
```bash
# Install test dependencies
poetry install --with dev

# Run all tests
poetry run pytest

# Run tests with coverage report
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_auth.py

# Run tests with verbose output
poetry run pytest -v

# Run async tests only
poetry run pytest -k "async"
```

### Test Categories
- **Unit Tests**: Individual function/method testing
- **Integration Tests**: Database and external service integration
- **API Tests**: Complete endpoint testing with test client
- **Authentication Tests**: JWT and permission testing

### Test Coverage
Aim for >90% test coverage on:
- Business logic in `service_layer/`
- API endpoints in `routers/`
- Database operations
- Authentication flows

## 🚀 Deployment

### Docker Production

```bash
# Build production image
docker build -t graintrade-backend:latest .

# Run with environment file
docker run -d \
  --name graintrade-backend \
  -p 8000:8000 \
  --env-file .env \
  graintrade-backend:latest
```

### Docker Compose

```bash
# Production deployment
docker-compose up -d backend

# Development with auto-reload
docker-compose -f docker-compose.dev.yaml up backend
```

### Production Checklist

- [ ] Set `DEBUG=false` in environment
- [ ] Use strong `SECRET_KEY` (64+ characters)
- [ ] Configure secure database credentials
- [ ] Set up SSL/TLS termination (via reverse proxy)
- [ ] Configure CORS origins properly
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy for PostgreSQL
- [ ] Set up health checks and auto-restart

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | - | ✅ |
| `REDIS_URL` | Redis connection string | - | ✅ |
| `RABBITMQ_URL` | RabbitMQ connection string | - | ✅ |
| `SECRET_KEY` | JWT signing key | - | ✅ |
| `DEBUG` | Enable debug mode | `false` | ❌ |
| `CORS_ORIGINS` | Allowed CORS origins | `[]` | ❌ |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiration | `30` | ❌ |
| `MAIL_SERVER` | SMTP server | - | ✅ |
| `MAIL_USERNAME` | SMTP username | - | ✅ |
| `MAIL_PASSWORD` | SMTP password | - | ✅ |

### Database Configuration

```python
# PostgreSQL with connection pooling
DATABASE_URL = "postgresql+asyncpg://user:pass@host:5432/db"

# Connection pool settings
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 30
DATABASE_POOL_TIMEOUT = 30
```

## 📊 Monitoring & Observability

### Health Checks
```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health with dependencies
curl http://localhost:8000/health?detail=true
```

### Logging
- **Structured Logging**: JSON format for production
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Request Tracking**: Correlation IDs for request tracing

### Metrics
- **Application Metrics**: Request count, response time, error rate
- **Business Metrics**: User registrations, item creations, payments
- **Infrastructure Metrics**: Database connections, Redis hits/misses

## 🛡️ Security

### Authentication & Authorization
- **JWT Tokens**: Access and refresh token pattern
- **Password Security**: bcrypt hashing with salt
- **Rate Limiting**: Redis-based request throttling
- **CORS**: Configurable cross-origin resource sharing

### Data Protection
- **Input Validation**: Pydantic schemas for all inputs
- **SQL Injection Prevention**: SQLAlchemy parameterized queries
- **XSS Protection**: Automatic output escaping
- **CSRF Protection**: Token-based protection for state-changing operations

### API Security
- **HTTPS Only**: Force SSL in production
- **Security Headers**: HSTS, CSP, X-Frame-Options
- **API Versioning**: Structured versioning strategy
- **Error Handling**: Safe error messages without sensitive data

## 🔄 Database Operations

### Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Custom SQL Functions
The backend includes PostgreSQL functions for:
- Subscription usage tracking
- Geospatial operations
- Performance-optimized queries

```sql
-- Example: Check user subscription limits
SELECT check_subscription_limits(user_id, 'premium');

-- Geospatial search
SELECT * FROM items_within_radius(lat, lng, radius_km);
```

## 🚀 Performance Optimization

### Database
- **Indexing**: Proper indexes on searchable fields
- **Query Optimization**: Use of async queries and joins
- **Connection Pooling**: Configured for high concurrency
- **PostGIS**: Optimized geospatial queries

### Caching Strategy
- **Redis**: Session data, frequently accessed data
- **Application Cache**: In-memory caching for static data
- **Database Query Cache**: PostgreSQL query result caching

### Async Operations
- **Async/Await**: Full async support throughout the application
- **Background Tasks**: RabbitMQ for long-running operations
- **Concurrent Processing**: Multiple async workers

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Install development dependencies: `poetry install --with dev`
4. Write tests for your changes
5. Ensure all tests pass: `poetry run pytest`
6. Follow PEP 8 style guidelines
7. Update documentation as needed
8. Submit a pull request

### Development Guidelines
- **Code Style**: Follow PEP 8, use black formatter
- **Type Hints**: Use type annotations throughout
- **Documentation**: Docstrings for all public functions
- **Testing**: Write tests for new functionality
- **Async**: Use async/await for I/O operations

## 📄 License

This project is licensed under the MIT - see the [LICENSE](../LICENSE) file for details.

## 📧 Support

For support and questions:
- **Email**: kivaschenko@protonmail.com
- **Issues**: [GitHub Issues](https://github.com/kivaschenko/graintrade-info/issues)
- **Documentation**: Check the `/docs` endpoint when running

---

**Part of the GrainTrade platform** 🌾
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