# GrainTrade Data Pipeline Microservice

A comprehensive data ingestion, transformation, and analytics pipeline for commodity price prediction in the Black Sea region. This microservice implements the Medallion Architecture (Bronze, Silver, Gold layers) using Apache Spark and Delta Lake.

## 🎯 Overview

The Data Pipeline microservice processes multiple data sources including:
- Historical commodity prices from World Bank statistics
- Weather data affecting crop yields
- News about conflicts and wars impacting trade
- Real-time prices from specialized sites, Telegram channels, and ad dashboards

It transforms raw data through three layers:
- **Bronze Layer**: Raw data ingestion from various formats (CSV, JSON, Parquet)
- **Silver Layer**: Cleaned and validated data
- **Gold Layer**: Analytics-ready data optimized for ML model training

## 🏗️ Architecture

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **API Framework** | FastAPI | RESTful API endpoints |
| **Database** | PostgreSQL | Metadata and processed results storage |
| **ORM** | SQLAlchemy | Database models and queries |
| **Migrations** | Alembic | Database schema versioning |
| **Data Processing** | Apache Spark 4.1+ | Distributed data transformation |
| **Data Lake** | Delta Lake | ACID transactions for data lake |
| **Orchestration** | Apache Airflow (planned) | Workflow scheduling |
| **Container Runtime** | Docker | Service deployment |

### Medallion Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Bronze    │───▶│   Silver    │───▶│    Gold     │
│  (Raw Data) │    │  (Cleaned)  │    │ (Analytics) │
└─────────────┘    └─────────────┘    └─────────────┘
      │                   │                   │
      ▼                   ▼                   ▼
  Delta Tables       Delta Tables        Delta Tables
  - CSV files        - Validated        - Wheat
  - JSON feeds       - Deduplicated     - Corn
  - Parquet          - Standardized     - Barley
                                        - etc.
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 15+
- Java 11+ (for Spark)
- Docker & Docker Compose (optional)

### Installation

1. **Clone the repository**
   ```bash
   cd /home/ikost/Projects/graintrade-info/data-pipeline
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up database**
   ```sql
   CREATE DATABASE analytic_db;
   CREATE USER data_analytic WITH ENCRYPTED PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE analytic_db TO data_analytic;
   ```

6. **Run migrations**
   ```bash
   alembic upgrade head
   ```

### Running the Service

**Development Mode:**
```bash
python -m app.main
# or
uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
```

**Production Mode:**
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8004
```

**With Docker:**
```bash
docker-compose up --build
```

### Spark Configuration

For standalone Spark cluster:
```bash
export SPARK_MASTER='spark://spark-master:7077'
export PYSPARK_PYTHON=/path/to/venv/bin/python
export PYSPARK_DRIVER_PYTHON=$PYSPARK_PYTHON
```

For local mode (development):
```bash
export SPARK_MASTER='local[*]'
```

## 📖 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

### Key Endpoints

#### Health Check
```bash
GET /health              # Basic health status
GET /health/database     # Database connectivity
GET /health/spark        # Spark connectivity
```

#### Data Sources Management
```bash
POST   /data-sources     # Register new data source
GET    /data-sources     # List all data sources
GET    /data-sources/{id} # Get specific data source
PATCH  /data-sources/{id} # Update data source
DELETE /data-sources/{id} # Delete data source
```

#### Data Ingestion
```bash
POST /ingestion/start    # Start ingestion job
GET  /ingestion/jobs     # List all jobs
GET  /ingestion/jobs/{job_id}  # Get job status
```

#### Commodities Data
```bash
POST /commodities        # Create commodity record
GET  /commodities        # List commodities (with filters)
GET  /commodities/{id}   # Get specific commodity
DELETE /commodities/{id} # Delete commodity
```

## 💾 Data Models

### Data Source
Tracks metadata about data sources:
- Name, type (CSV, JSON, API, Telegram, web scraping)
- Connection details (URL, file path, API endpoint)
- Update frequency
- Configuration (flexible JSON)
- Status tracking

### Commodity
Represents processed commodity price data:
- Name (wheat, corn, barley, etc.)
- Region (Ukraine, Russia, Black Sea)
- Price with currency and unit
- Quality parameters (protein, moisture content)
- Temporal data
- Source tracking

### Ingestion Log
Tracks data ingestion operations:
- Job ID and status
- Records processed (read/written/failed)
- Execution time
- Error tracking
- Input/output paths

### Prediction
ML model predictions for commodity prices:
- Predicted price with confidence intervals
- Model metadata (name, version, features)
- Prediction horizon
- Actual values for evaluation

## 🔄 Data Pipeline Workflow

### 1. Register Data Source
```bash
curl -X POST "http://localhost:8001/data-sources" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "WorldBank Historical Prices",
    "source_type": "csv",
    "file_path": "/data/sources/worldbank_prices.csv",
    "update_frequency": "daily",
    "config": {"commodity_name": "wheat"}
  }'
```

### 2. Ingest to Bronze Layer
```bash
curl -X POST "http://localhost:8001/ingestion/start" \
  -H "Content-Type: application/json" \
  -d '{
    "data_source_id": 1,
    "layer": "bronze"
  }'
```

### 3. Transform to Silver Layer
```bash
curl -X POST "http://localhost:8001/ingestion/start" \
  -H "Content-Type: application/json" \
  -d '{
    "data_source_id": 1,
    "layer": "silver"
  }'
```

### 4. Create Gold Tables
```bash
curl -X POST "http://localhost:8001/ingestion/start" \
  -H "Content-Type: application/json" \
  -d '{
    "data_source_id": 1,
    "layer": "gold"
  }'
```

## 🧪 Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=data_pipeline tests/

# Linting
black src/
ruff check src/
```

## 📁 Project Structure

```
data-pipeline/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   ├── logger.py            # Logging setup
│   ├── models/              # SQLAlchemy models
│   │   ├── commodity_model.py
│   │   ├── data_source_model.py
│   │   ├── ingestion_log_model.py
│   │   └── prediction_model.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── commodity_schema.py
│   │   ├── data_source_schema.py
│   │   ├── ingestion_schema.py
│   │   └── prediction_schema.py
│   ├── routers/             # API routes
│   │   ├── commodity_router.py
│   │   ├── data_source_router.py
│   │   ├── ingestion_router.py
│   │   └── health_router.py
│   └── spark_services/      # Spark processing
│       ├── spark_session.py
│       ├── bronze_layer.py
│       ├── silver_layer.py
│       └── gold_layer.py
├── alembic/                     # Database migrations
│   └── versions/
│       └── 001_initial_migration.py
├── tests/                  # Unit and integration tests
├── pyproject.toml          # Project dependencies
├── alembic.ini             # Alembic configuration
├── Dockerfile              # Container definition
├── .env.example            # Environment template
└── README.md               # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |
| `SPARK_MASTER` | Spark master URL | `local[*]` |
| `SPARK_APP_NAME` | Application name in Spark | `GrainTrade-DataPipeline` |
| `BRONZE_LAYER_PATH` | Path to bronze Delta tables | `/data/delta/bronze` |
| `SILVER_LAYER_PATH` | Path to silver Delta tables | `/data/delta/silver` |
| `GOLD_LAYER_PATH` | Path to gold Delta tables | `/data/delta/gold` |
| `API_HOST` | API server host | `0.0.0.0` |
| `API_PORT` | API server port | `8001` |
| `ENV` | Environment (development/production) | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |

## 🛠️ Development

### Adding New Data Sources

1. Register data source via API or database
2. Implement custom reader if needed in `spark_services/bronze_layer.py`
3. Add transformation rules in `spark_services/silver_layer.py`
4. Define business logic in `spark_services/gold_layer.py`

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 📊 Monitoring

### Metrics Endpoints
- Application metrics: `/metrics` (Prometheus format)
- Health checks: `/health/*`
- Ingestion logs: `/ingestion/jobs`

### Logging
Structured logging to stdout/stderr with configurable levels:
- DEBUG: Detailed information
- INFO: General information
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical failures

## 🔒 Security Considerations

- [ ] API authentication (JWT tokens)
- [ ] Rate limiting
- [ ] Input validation (Pydantic schemas)
- [ ] SQL injection protection (SQLAlchemy ORM)
- [ ] Secrets management (environment variables)
- [ ] HTTPS in production
- [ ] CORS configuration

## 🚧 Roadmap

### Phase 1: Core Pipeline ✅
- [x] Bronze layer ingestion
- [x] Silver layer transformation
- [x] Gold layer analytics tables
- [x] FastAPI endpoints
- [x] Database models

### Phase 2: Enhanced Processing (In Progress)
- [ ] Real-time streaming ingestion
- [ ] Advanced data quality checks
- [ ] Multiple commodity support
- [ ] Weather data integration
- [ ] News sentiment analysis

### Phase 3: ML Integration
- [ ] ML model training pipeline
- [ ] Price prediction endpoints
- [ ] Model versioning
- [ ] Feature engineering
- [ ] Model performance tracking

### Phase 4: Operations
- [ ] Airflow DAGs for orchestration
- [ ] Monitoring dashboards
- [ ] Alerting system
- [ ] Data lineage tracking
- [ ] Automated testing

## 📝 License

Apache-2.0 License

## 👥 Contributors

- K. Ivashchenko (civaschenko@yahoo.com)

## 🔗 Related Services

- **Backend API**: Main GrainTrade application
- **Frontend**: Vue.js web application
- **Parsers**: Data collection services
- **Notifications**: Alert system
- **Chat Room**: Real-time communication

## 📞 Support

For issues and questions:
- Open an issue in the repository
- Contact: civaschenko@yahoo.com
