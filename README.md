# 🌾 GrainTrade - Agricultural Trading Platform
# 🌾 GrainTrade - Agricultural Trading Platform

> Note for reviewers and potential employers
>
> This repository is now public as part of my portfolio. GrainTrade is my ongoing pet project: a production-deployed, microservices-based marketplace for agricultural commodities in Ukraine. You can explore the live site at https://graintrade.info/.
>
> Highlights:
> - End-to-end ownership: architecture, backend (FastAPI), frontend (Vue 3), infrastructure, CI/CD.
> - Event-driven microservices: RabbitMQ, Redis caching, WebSocket real-time chat/notifications.
> - Observability and security: Prometheus + Grafana, Apache reverse proxy, SSL, rate limiting.
>
> What to expect:
> - Active development: some features are evolving; APIs and UI may change.
> - Clear structure: each service lives in its own folder with dedicated Dockerfiles and docs.
> - Quick tour: start with the sections “Architecture Overview”, “Features”, and “Quick Start”.
>
> Useful links:
> - Production: https://graintrade.info/
> - API Docs: https://api.graintrade.info/docs
> - Repo Roadmap: TECH_STACK_AND_ROADMAP.md
>
> I’m happy to walk through design decisions, trade-offs, and next milestones. Feel free to reach out via email listed below.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-Jenkins-orange)](Jenkinsfile)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](docker-compose.yaml)

A modern microservices-based platform for Ukrainian farmers to trade agricultural commodities including grain, seeds, fertilizers, and fuel. Built with FastAPI, Vue.js, and event-driven architecture using RabbitMQ.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │    │   Landing       │    │   Apache        │
│   (Vue.js)      │    │   Service       │    │   Reverse       │
│   Port: 8080    │    │   Port: 8003    │    │   Proxy         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Backend      │    │   Chat Room     │    │ Notifications   │
│   (FastAPI)     │    │   Service       │    │   Service       │
│   Port: 8000    │    │   Port: 8001    │    │   Port: 8002    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │    RabbitMQ     │    │     Redis       │
│   Database      │    │   Message       │    │    Cache        │
│   Port: 5432    │    │   Queue         │    │   Port: 6379    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Features

### Core Platform
- **Agricultural Trading**: Buy/sell grain, seeds, fertilizers, fuel
- **User Management**: Registration, authentication, subscription plans
- **Geospatial Search**: Location-based item filtering with Mapbox integration
- **Real-time Communication**: WebSocket-based chat system
- **Payment Processing**: Integrated payment gateway
- **Multilingual Support**: Ukrainian and English interfaces

### Technical Features
- **Microservices Architecture**: Independent, scalable services
- **Event-Driven**: RabbitMQ message queue for service communication
- **Real-time Updates**: WebSocket connections for live data
- **Caching**: Redis for performance optimization
- **Monitoring**: Prometheus + Grafana observability stack
- **CI/CD**: Jenkins pipeline with Docker Hub integration

## 📦 Technology Stack

### Backend Services
- **Framework**: FastAPI 0.115.4+ (Python 3.12)
- **Database**: PostgreSQL with asyncpg driver
- **Cache**: Redis with async support
- **Message Queue**: RabbitMQ with aio-pika
- **Authentication**: JWT tokens with bcrypt
- **API Documentation**: OpenAPI/Swagger auto-generation

### Frontend
- **Framework**: Vue.js 3.5+ with Composition API
- **Build Tool**: Vue CLI with Webpack
- **UI Framework**: Bootstrap 5.3+
- **Maps**: Mapbox GL JS 3.8+
- **HTTP Client**: Axios
- **State Management**: Vuex 4
- **Routing**: Vue Router 4
- **Internationalization**: Vue I18n

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Web Server**: Apache2 with SSL (Let's Encrypt)
- **Monitoring**: Prometheus, Grafana, Node Exporter
- **Security**: Fail2Ban, UFW firewall
- **CI/CD**: Jenkins with Docker Hub registry

### Communication
- **Message Queue**: RabbitMQ for service-to-service communication
- **WebSocket**: Real-time chat and notifications
- **Email**: SMTP integration for notifications
- **External APIs**: Payment gateways, geocoding services

## 🏗️ Services Architecture

### Core Services

| Service | Port | Description | Technology |
|---------|------|-------------|------------|
| **Backend** | 8000 | Main API service | FastAPI, PostgreSQL, Redis |
| **Chat Room** | 8001 | Real-time messaging | FastAPI, WebSocket, RabbitMQ |
| **Notifications** | 8002 | Email & push notifications | FastAPI, SMTP, Telegram |
| **Frontend** | 8080 | Web application | Vue.js, Nginx |
| **Landing** | 8003 | Marketing pages | Flask, Jinja2 |

### Supporting Services

| Service | Port | Description |
|---------|------|-------------|
| **PostgreSQL** | 5432 | Primary database |
| **Redis** | 6379 | Cache & sessions |
| **RabbitMQ** | 5672/15672 | Message queue |
| **Prometheus** | 9090 | Metrics collection |
| **Grafana** | 3000 | Monitoring dashboard |

### Utility Services
- **Cron Services**: Subscription management and automated tasks
- **Parsers**: Data import and commodity price updates
- **Apache Files**: Web server configuration and security

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 16+ (for development)
- Python 3.12+ (for development)
- Git

### Production Deployment

1. **Clone the repository**
```bash
git clone https://github.com/kivaschenko/graintrade-info.git
cd graintrade-info
```

2. **Configure environment variables**
```bash
# Backend services
cp backend/sample_env backend/.env
cp chat-room/.env.example chat-room/.env
cp notifications/.env.example notifications/.env

# Frontend
cp frontend/.env.example frontend/.env.production
```

3. **Start all services**
```bash
docker-compose up -d --build
```

4. **Verify deployment**
```bash
docker-compose logs
curl http://localhost:8000/health
```

### Development Mode

1. **Start infrastructure services**
```bash
cd rabbitmq-init
docker-compose up -d
```

2. **Run backend services**
```bash
# Terminal 1 - Main Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
fastapi dev

# Terminal 2 - Chat Service
cd chat-room
source venv/bin/activate
pip install -r requirements.txt
fastapi dev --port 8001

# Terminal 3 - Notifications
cd notifications
source venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

3. **Run frontend**
```bash
# Terminal 4 - Frontend
cd frontend
npm install
npm run serve
```

4. **Access the application**
- Frontend: http://localhost:8080
- API Documentation: http://localhost:8000/docs
- Chat API: http://localhost:8001/docs
- Notifications API: http://localhost:8002/docs

## � Configuration

### Environment Variables

Each service requires specific environment variables:

#### Backend (.env)
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
REDIS_URL=redis://localhost:6379
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
JWT_SECRET=your_jwt_secret
MAPBOX_ACCESS_TOKEN=your_mapbox_token
SMTP_PASSWORD=your_smtp_password
```

#### Frontend (.env.production)
```env
VUE_APP_API_URL=https://api.graintrade.info
VUE_APP_CHAT_URL=https://chat.graintrade.info
VUE_APP_MAPBOX_TOKEN=your_mapbox_token
VUE_APP_WEBSOCKET_URL=wss://chat.graintrade.info/ws
```

### Service Health Checks

All services include health check endpoints:
- Backend: `GET /health`
- Chat Room: `GET /health`
- Notifications: `GET /health`
- Landing: `GET /health`

## 📊 Monitoring & Observability

### Metrics Collection
- **Prometheus**: Collects metrics from all services
- **Node Exporter**: System metrics
- **PostgreSQL Exporter**: Database metrics
- **Redis Exporter**: Cache metrics

### Dashboards
- **Grafana**: http://localhost:3000 (admin/admin123)
- Pre-configured dashboards for system and application metrics

### Logging
- Centralized logging with structured JSON logs
- Service-specific log levels and rotation
- Health check monitoring with alerts

## 🔒 Security

### Infrastructure Security
- **SSL/TLS**: Let's Encrypt certificates
- **Firewall**: UFW with restricted access
- **Fail2Ban**: Intrusion prevention
- **Security Headers**: CORS, CSP, HSTS

### Application Security
- **Authentication**: JWT tokens with expiration
- **Password Hashing**: bcrypt with salt
- **Input Validation**: Pydantic schemas
- **Rate Limiting**: Redis-based throttling
- **SQL Injection Prevention**: Parameterized queries

## 🚢 Deployment

### CI/CD Pipeline
1. **Build**: Docker images for each service
2. **Test**: Automated testing with pytest
3. **Push**: Images to Docker Hub registry
4. **Deploy**: Docker Compose on production server
5. **Monitor**: Health checks and rollback capability

### Production Infrastructure
- **Server**: Hetzner AX41-NVMe recommended
- **Load Balancer**: Apache2 reverse proxy
- **SSL**: Automated Let's Encrypt renewal
- **Backup**: Database and volume backups
- **Monitoring**: 24/7 health monitoring

## 📁 Project Structure

```
graintrade-info/
├── apache_files/          # Apache2 configuration
├── backend/               # Main FastAPI service
├── chat-room/            # Real-time messaging service
├── cron_services/        # Scheduled tasks
├── frontend/             # Vue.js web application
├── landing-service/      # Marketing website
├── monitoring/           # Prometheus & Grafana config
├── notifications/        # Email & push notifications
├── parsers/             # Data import utilities
├── postgres-init/       # Database initialization
├── rabbitmq-init/       # Message queue setup
├── scripts/             # Deployment scripts
├── docker-compose.yaml  # Production deployment
├── docker-compose.dev.yaml  # Development setup
├── Jenkinsfile         # CI/CD pipeline
└── README.md           # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Follow the coding standards for each service
4. Write tests for new functionality
5. Update documentation as needed
6. Submit a pull request

### Development Guidelines
- Follow PEP 8 for Python code
- Use Vue.js style guide for frontend
- Write comprehensive tests
- Update API documentation
- Use conventional commit messages

## 📄 License

This project is licensed under the MIT - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Production**: [graintrade.info](https://graintrade.info)
- **API Documentation**: [api.graintrade.info/docs](https://api.graintrade.info/docs)
- **Repository**: [GitHub](https://github.com/kivaschenko/graintrade-info)
- **Issues**: [GitHub Issues](https://github.com/kivaschenko/graintrade-info/issues/new)

## 📧 Support

For support and questions:
- Email: kivaschenko@protonmail.com
- GitHub Issues: [Create an issue](https://github.com/kivaschenko/graintrade-info/issues/new)

---

**Made with ❤️ for Ukrainian farmers** 🇺🇦  
Project by [yourname or startup]