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
> - Architecture audit: [ARCHITECTURE_AUDIT.md](ARCHITECTURE_AUDIT.md)
> - Business roadmap: [docs/ProjectAudit_BusinessRoadmap.md](docs/ProjectAudit_BusinessRoadmap.md)
> - **Licensing**: Available under dual licensing (AGPL v3 open-source + commercial). See [License](#license) section.
>
> I’m happy to walk through design decisions, trade-offs, and next milestones. Feel free to reach out via email listed below.

[![License](https://img.shields.io/badge/license-AGPL%20v3%20%2B%20Commercial-blue.svg)](LICENSE)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue)](.github/workflows/deploy.yml)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](docker-compose.yaml)

GrainTrade is a microservices platform for agricultural commodity trading in Ukraine.

- Production: https://graintrade.info/
- Architecture audit: [ARCHITECTURE_AUDIT.md](ARCHITECTURE_AUDIT.md)
- Business roadmap: [docs/ProjectAudit_BusinessRoadmap.md](docs/ProjectAudit_BusinessRoadmap.md)

## Services

| Service | Port | Role |
|---|---:|---|
| Backend | 8000 | Main API |
| Chat Room | 8001 | Real-time chat |
| Notifications | 8002 | Email/notification workflows |
| Landing Service | 8003 | Marketing pages |
| Data Pipeline | 8004 | Forecasting and analytics API |
| Frontend | 8080 | Vue web app |

Infrastructure: PostgreSQL (5432), Redis (6379), RabbitMQ (5672/15672).

## Quick Start (Local via Docker)

### Prerequisites

- Docker and Docker Compose
- Git

### 1. Clone

```bash
git clone https://github.com/kivaschenko/graintrade-info.git
cd graintrade-info
```

### 2. Create environment files

```bash
cp backend/sample_env backend/.env
cp chat-room/.env.prod.example chat-room/.env
cp notifications/.env.prod.example notifications/.env
cp data-pipeline/.env.example data-pipeline/.env
```

Create `frontend/.env.production` manually (required by compose) with at least:

```env
VUE_APP_BACKEND_URL=http://localhost:8000
VUE_APP_CHAT_HTTP_URL=http://localhost:8001
VUE_APP_CHAT_WS_URL=ws://localhost:8001
VUE_APP_DATA_PIPELINE_API_URL=http://localhost:8004
VUE_APP_MAPBOX_TOKEN=your_mapbox_token
```

### 3. Start the stack

```bash
docker-compose up -d --build
```

### 4. Verify

```bash
docker-compose ps
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
```

Main URLs:

- Frontend: http://localhost:8080
- Backend docs: http://localhost:8000/docs
- Chat docs: http://localhost:8001/docs
- Notifications docs: http://localhost:8002/docs
- Data Pipeline docs: http://localhost:8004/docs

## Production Compose

- Use [docker-compose.prod.yaml](docker-compose.prod.yaml) for prebuilt images.
- This file expects service env files under an `envs/` directory:
  - `envs/backend.env`
  - `envs/chat-room.env`
  - `envs/notifications.env`
  - `envs/data-pipeline.env`

## Service Documentation

- [backend/README.md](backend/README.md)
- [chat-room/README.md](chat-room/README.md)
- [notifications/README.md](notifications/README.md)
- [data-pipeline/README.md](data-pipeline/README.md)
- [frontend/README.md](frontend/README.md)
- [landing-service/README.md](landing-service/README.md)
- [monitoring/README.md](monitoring/README.md)

## Repository Layout

```text
graintrade-info/
|- backend/
|- chat-room/
|- notifications/
|- data-pipeline/
|- frontend/
|- landing-service/
|- monitoring/
|- cron_services/
|- parsers/
|- docker-compose.yaml
|- docker-compose.prod.yaml
`- README.md
```

## Development Notes

- Root compose file [docker-compose.yaml](docker-compose.yaml) builds services from source.
- CI/CD workflow is in [.github/workflows/deploy.yml](.github/workflows/deploy.yml).
- Monitoring-related helper scripts live in the repository root and [monitoring](monitoring).

## Contributing

1. Create a feature branch.
2. Keep changes scoped to one service when possible.
3. Add or update tests and docs for behavioral changes.
4. Open a pull request with a clear summary.

## License

GrainTrade is available under a **dual-license model**:

### 1. **Open Source License (AGPL v3)**
Free to use, modify, and distribute under the GNU Affero General Public License v3.0.
See [LICENSE](LICENSE) for full terms.

- ✅ Self-hosted deployments
- ✅ Internal use and forks (with source sharing for network use)
- ✅ Non-commercial projects

### 2. **Commercial License**
For businesses and teams that want proprietary use without copyleft obligations.

- 💼 SaaS deployments with competitive modifications
- 💼 Proprietary integrations
- 💼 Closed-source derivatives

[Learn more about commercial licensing](COMMERCIAL_LICENSE.md)

## Contact

- **License Inquiry**: kivaschenko@protonmail.com (subject: "Commercial License")
- Email: kivaschenko@protonmail.com
- Issues: https://github.com/kivaschenko/graintrade-info/issues/new
