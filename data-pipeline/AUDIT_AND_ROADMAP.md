# Data Pipeline Microservice - Audit & Improvement Plan

**Date**: January 9, 2026  
**Status**: In Progress  
**Approach**: KISS Principle (Keep It Simple, Stupid)

---

## 🔍 Executive Summary

The data-pipeline microservice is the core analytics engine for GrainTrade platform, processing commodity prices from multiple sources, transforming data through medallion architecture (Bronze → Silver → Gold), and generating price forecasts using linear regression models.

---

## ✅ Current Implementation Status

### ✓ Completed Features

1. **Data Ingestion (Bronze Layer)**
   - Yahoo Finance parser for global futures (CBOT)
   - Yahoo Finance parser for commodity ETFs (NYSE)
   - Investing.com integration for additional data sources
   - Parquet file exports with timestamps
   - Delta Lake table persistence

2. **Data Transformation (Silver Layer)**
   - Feature engineering (MA-7, MA-30, volatility, momentum)
   - Currency conversion (USD → UAH) via NBU API
   - Price normalization (cents per bushel → USD per ton)
   - Data cleaning and validation
   - Parquet + Delta Lake dual storage

3. **Commodity Tracking**
   - PostgreSQL storage of latest commodity prices
   - UPSERT logic to avoid duplicates
   - Metadata tracking (region, variety, quality)
   - Source attribution

4. **Prediction Model**
   - Linear trend regression (simple & effective)
   - Multi-horizon forecasts (1-7 days ahead)
   - Confidence intervals (based on historical volatility)
   - Feature tracking for model interpretability

5. **Database Models**
   - `commodities` table for current prices
   - `predictions` table for forecasts
   - `data_sources` table for source metadata
   - `ingestion_logs` table for pipeline tracking

6. **API Endpoints** (NEW)
   - `/forecasts/` - Get filtered forecasts
   - `/forecasts/homepage` - Simplified forecasts for frontend
   - `/forecasts/{commodity}` - Detailed commodity forecasts

7. **RabbitMQ Integration** (NEW)
   - Predictions published to `predictions_queue`
   - Async publishing with aio-pika
   - Structured messages for notifications microservice

---

## 🐛 Critical Bugs Fixed

### 1. **Series Object in SQLAlchemy** (RESOLVED ✓)
**Problem**: Pandas Series objects were passed to SQLAlchemy filters, causing `ProgrammingError: can't adapt type 'Series'`.

**Root Cause**: 
```python
region = last_row.get("region", "Global")  # Returns Series, not scalar
Prediction.region == payload["region"]     # Series passed to SQL
```

**Solution**: 
```python
region_value = _ensure_scalar(last_row.get("region", "Global")) or "Global"
# Extract ALL scalars before database operations
```

**Files Modified**: `app/services/grain_forecast_pipeline.py`

**Impact**: Pipeline now completes successfully without database errors.

---

## 🎯 Architecture Assessment

### Strengths
1. **Medallion Architecture**: Clean separation of Bronze → Silver → Gold layers
2. **Dual Storage**: Parquet files (portable) + Delta Lake (ACID)
3. **Simple Model**: Linear regression is fast, interpretable, and effective for short-term trends
4. **Modular Design**: Parsers, storage, and services properly separated
5. **Async-Ready**: RabbitMQ integration uses async/await

### Areas for Improvement
1. **Delta Lake Compatibility**: Spark 4.1 + Delta Lake version mismatch (Java errors)
2. **Ukrainian Market Data**: Missing local market parsers (APK-Inform, UkrAgroConsult)
3. **Currency Rates**: Not stored as time series in silver layer
4. **Storage Integration**: Hetzner S3 implemented but not integrated into pipeline
5. **Batch Processing**: No scheduled runs (need Airflow/cron integration)

---

## 📋 Improvement Roadmap

### Phase 1: Core Fixes & Enhancements (Current Sprint)

#### 1.1 Ukrainian Market Data Sources ⏳
**Priority**: HIGH  
**Complexity**: MEDIUM

**Implementation**:
- Enhance `app/parser_services/graintradecomua_parser.py`
- Add APK-Inform parser (JSON API)
- Add ProAgro parser (table scraping)
- Normalize prices to common currency/unit

**File to Create**:
```python
# app/parser_services/apk_inform_parser.py
class APKInformParser(BaseParser):
    """Parse commodity prices from APK-Inform (Ukraine)"""
    def parse(self) -> pd.DataFrame:
        # Fetch from APK-Inform API
        # Normalize to standard schema
        # Return DataFrame
```

**Data Schema**:
```python
{
    "commodity": "Wheat",
    "region": "Ukraine-Odesa",
    "price": 5200.0,
    "currency": "UAH",
    "unit": "ton",
    "quality": "3rd class",
    "date": "2026-01-09",
    "source": "APK-Inform"
}
```

---

#### 1.2 Hetzner Storage Integration ⏳
**Priority**: MEDIUM  
**Complexity**: LOW

**Implementation**:
Update `grain_forecast_pipeline.py` to upload artifacts:

```python
def _write_parquet_artifact(self, df: pd.DataFrame, layer_name: str) -> Path:
    # ... existing code ...
    
    # Upload to Hetzner S3
    if settings.HETZNER_STORAGE_ACCESS_KEY:
        try:
            from app.storage_services.hetzner_storage import upload_file_to_hetzner_s3
            object_key = f"grain_forecast/{layer_name}/{file_path.name}"
            upload_file_to_hetzner_s3(
                str(file_path),
                settings.HETZNER_STORAGE_BUCKET,
                object_key
            )
            logger.info(f"Uploaded {layer_name} to Hetzner: {object_key}")
        except Exception as exc:
            logger.warning(f"Failed to upload to Hetzner: {exc}")
    
    return file_path
```

---

#### 1.3 Currency Exchange Rates in Silver Layer ⏳
**Priority**: MEDIUM  
**Complexity**: LOW

**Implementation**:
Store exchange rates as separate table/feature:

```python
def _fetch_currency_rates(self, start_date: datetime) -> pd.DataFrame:
    """Fetch USD/UAH and EUR/UAH rates from NBU."""
    rates = []
    current = start_date
    while current <= datetime.now(timezone.utc):
        usd_uah = fetch_usd_to_uah(current)
        eur_uah = fetch_eur_to_uah(current)
        rates.append({
            "date": current,
            "usd_uah": usd_uah,
            "eur_uah": eur_uah,
        })
        current += timedelta(days=1)
    return pd.DataFrame(rates)
```

**Merge into silver DataFrame**:
```python
features_df = features_df.merge(rates_df, on="date", how="left")
```

---

### Phase 2: Production Readiness (Next Sprint)

#### 2.1 Scheduled Execution
**Tool**: Apache Airflow or simple cron

**Airflow DAG Example**:
```python
# airflow/dags/grain_forecast_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

def run_pipeline():
    from app.services.grain_forecast_pipeline import GrainForecastPipeline
    pipeline = GrainForecastPipeline()
    pipeline.run()

dag = DAG(
    'grain_forecast_pipeline',
    schedule_interval='0 6 * * *',  # Daily at 6 AM
    start_date=datetime(2026, 1, 1),
    catchup=False,
)

task = PythonOperator(
    task_id='run_forecast',
    python_callable=run_pipeline,
    dag=dag,
)
```

---

#### 2.2 Delta Lake Compatibility Fix
**Problem**: Spark 4.1.0 + Delta Lake version mismatch

**Solution**: Downgrade Spark to 3.5.x or upgrade Delta Lake

**pyproject.toml**:
```toml
[tool.poetry.dependencies]
pyspark = "3.5.3"  # Stable version
delta-spark = "3.2.1"  # Compatible
```

---

#### 2.3 Model Enhancements (Keep Simple!)
**Principle**: Don't overcomplicate - linear regression is sufficient

**Optional Enhancements**:
1. **Weighted Moving Average**: Recent data more important
2. **Seasonal Adjustment**: Account for harvest cycles
3. **External Signals**: Oil prices, weather indices

**Example**:
```python
def _weighted_moving_average(self, series: pd.Series, window: int = 30) -> float:
    """Calculate exponentially weighted moving average."""
    weights = np.exp(np.linspace(-1., 0., window))
    weights /= weights.sum()
    return np.convolve(series.tail(window), weights, mode='valid')[0]
```

---

### Phase 3: Advanced Features (Future)

#### 3.1 Real-time Streaming (Kafka + Spark Streaming)
- Process prices as they arrive
- Update predictions continuously
- Sub-second latency

#### 3.2 Multi-Model Ensemble
- Linear Regression (trend)
- ARIMA (seasonality)
- Prophet (holidays)
- Average predictions with confidence weighting

#### 3.3 A/B Testing Framework
- Track prediction accuracy per model
- Switch models based on performance
- Store metrics in `model_performance` table

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                             │
├─────────────────────────────────────────────────────────────┤
│ • Yahoo Finance (CBOT Futures)                              │
│ • Yahoo Finance (ETFs)                                      │
│ • Investing.com (Commodities)                               │
│ • GrainTrade.com.ua (Ukraine) ← TO ADD                      │
│ • APK-Inform (Ukraine) ← TO ADD                             │
│ • NBU API (Currency Rates)                                  │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│              BRONZE LAYER (Raw Ingestion)                   │
├─────────────────────────────────────────────────────────────┤
│ Storage:                                                    │
│ • /parsers_results/grain_forecast/bronze_*.parquet          │
│ • /data/delta/bronze/ (Delta Table)                         │
│ • Hetzner S3: graintrade-info/grain_forecast/bronze/        │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│          SILVER LAYER (Cleaned & Transformed)               │
├─────────────────────────────────────────────────────────────┤
│ Transformations:                                            │
│ • Feature engineering (MA-7, MA-30, volatility, momentum)   │
│ • Currency conversion (USD ↔ UAH)                           │
│ • Price normalization (bushel → ton)                        │
│ • Outlier removal & imputation                              │
│                                                             │
│ Storage:                                                    │
│ • /parsers_results/grain_forecast/silver_*.parquet          │
│ • /data/delta/silver/ (Delta Table)                         │
│ • Hetzner S3: graintrade-info/grain_forecast/silver/        │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│                GOLD LAYER (Analytics)                       │
├─────────────────────────────────────────────────────────────┤
│ Operations:                                                 │
│ • Sync to `commodities` table (PostgreSQL)                  │
│ • Generate forecasts (Linear Regression)                    │
│ • Persist to `predictions` table                            │
│ • Publish to RabbitMQ (predictions_queue)                   │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│                  CONSUMPTION LAYER                          │
├─────────────────────────────────────────────────────────────┤
│ • FastAPI Endpoints (/forecasts/homepage)                   │
│ • Notifications Microservice (Telegram bot)                 │
│ • Frontend (Vue.js homepage)                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔌 Integration Points

### 1. Frontend Integration
**Endpoint**: `GET /forecasts/homepage`

**Usage in Vue.js**:
```javascript
// frontend/src/components/ForecastWidget.vue
async fetchForecasts() {
  const response = await axios.get('https://api.graintrade.info/forecasts/homepage');
  this.forecasts = response.data;
}
```

**Display**:
```html
<div class="forecast-card" v-for="forecast in forecasts" :key="forecast.commodity">
  <h3>{{ forecast.commodity }}</h3>
  <div class="next-day">
    Tomorrow: ${{ forecast.next_day.price.toFixed(2) }}
    <span class="confidence">({{ (forecast.next_day.confidence * 100).toFixed(0) }}%)</span>
  </div>
  <div class="week-ahead">
    Week Ahead: ${{ forecast.week_ahead.price.toFixed(2) }}
    <span class="range">
      (${{ forecast.week_ahead.lower_bound.toFixed(2) }} - ${{ forecast.week_ahead.upper_bound.toFixed(2) }})
    </span>
  </div>
</div>
```

---

### 2. Notifications Integration
**Queue**: `predictions_queue`

**Message Format**:
```json
{
  "type": "grain_price_forecast",
  "commodity_name": "Wheat Futures",
  "region": "CBOT",
  "predicted_price": 175.88,
  "currency": "USD",
  "prediction_date": "2026-01-10T00:00:00+00:00",
  "prediction_horizon_days": 1,
  "confidence_score": 0.87,
  "lower_bound": 172.34,
  "upper_bound": 179.42,
  "model_name": "LinearTrendRegressor",
  "timestamp": "2026-01-09T12:34:56+00:00"
}
```

**Notifications Service Handler**:
```python
# notifications/app/handlers/forecast_handler.py
async def handle_forecast_notification(message: dict):
    """Send forecast to Telegram channel."""
    text = (
        f"📊 **Price Forecast**\n"
        f"Commodity: {message['commodity_name']}\n"
        f"Predicted Price: ${message['predicted_price']:.2f}\n"
        f"Date: {message['prediction_date'][:10]}\n"
        f"Confidence: {message['confidence_score']*100:.0f}%\n"
        f"Range: ${message['lower_bound']:.2f} - ${message['upper_bound']:.2f}"
    )
    await telegram_bot.send_message(settings.TELEGRAM_CHANNEL_ID, text)
```

---

## 🛠️ Development Workflow

### Running the Pipeline

**Manual Execution**:
```bash
cd /home/ikost/Projects/graintrade-info/data-pipeline
source venv/bin/activate
python -m app.services.grain_forecast_pipeline
```

**Check Results**:
```bash
# Artifacts
ls -lh parsers_results/grain_forecast/

# Database
psql -U data_analytic -d analytic_db -c "SELECT * FROM predictions ORDER BY created_at DESC LIMIT 10;"

# RabbitMQ Queue
rabbitmqctl list_queues name messages
```

**API Testing**:
```bash
# Health check
curl http://localhost:8004/health

# Get homepage forecasts
curl http://localhost:8004/forecasts/homepage | jq

# Get specific commodity
curl "http://localhost:8004/forecasts/Wheat%20Futures?days_ahead=7" | jq
```

---

### Testing Strategy

**Unit Tests**:
```python
# tests/test_grain_forecast_pipeline.py
def test_linear_trend_forecast():
    pipeline = GrainForecastPipeline()
    series = pd.Series([100, 105, 110, 115, 120])
    result = pipeline._linear_trend_forecast(series, window=5)
    
    assert len(result["predictions"]) == 7
    assert result["slope"] > 0  # Upward trend
    assert result["predictions"][0] > 120  # Continues trend
```

**Integration Tests**:
```python
def test_end_to_end_pipeline(test_db):
    pipeline = GrainForecastPipeline()
    summary = pipeline.run()
    
    assert summary["status"] == "completed"
    assert summary["records_ingested"] > 0
    assert summary["predictions_saved"] > 0
```

---

## 📈 Performance Metrics

### Current Performance
- **Pipeline Execution**: ~5-7 minutes (depends on API responses)
- **Data Volume**: ~500-1000 records per run
- **Prediction Generation**: ~49 forecasts (7 commodities × 7 days)
- **Database Operations**: ~3 commodity updates + 49 prediction upserts

### Optimization Opportunities
1. **Parallel API Calls**: Use `asyncio.gather()` for Yahoo Finance downloads
2. **Batch Inserts**: Use SQLAlchemy bulk operations
3. **Delta Table Caching**: Keep Spark session alive between runs
4. **Incremental Updates**: Only fetch new data since last run

---

## 🚨 Known Issues & Limitations

### 1. Delta Lake Compatibility
**Issue**: Java error `NoSuchMethodError: LogKey.$init$`  
**Workaround**: Parquet files still created successfully  
**Fix**: Upgrade to Spark 3.5.x (see Phase 2.2)

### 2. Limited Ukrainian Market Data
**Issue**: Only GrainTrade.com.ua implemented  
**Impact**: Missing local spot prices from farms/elevators  
**Fix**: Implement APK-Inform and ProAgro parsers (Phase 1.1)

### 3. No Real-time Updates
**Issue**: Pipeline runs manually  
**Impact**: Forecasts may be stale  
**Fix**: Set up cron job or Airflow DAG (Phase 2.1)

### 4. Simple Model
**Note**: Linear regression is intentionally simple (KISS principle)  
**Trade-off**: Good short-term accuracy, less effective for seasonal patterns  
**Acceptable**: For 1-7 day forecasts, linear trend is sufficient

---

## 💡 KISS Principle Applied

### What We AVOIDED (Good!)
- ❌ Complex neural networks (LSTM, Transformers)
- ❌ Microservices for each parser (unnecessary)
- ❌ Custom ML framework (use standard libraries)
- ❌ God classes with 1000+ lines
- ❌ Over-engineered abstractions

### What We DID (Good!)
- ✅ Simple linear regression (fast, interpretable)
- ✅ Modular parsers (one file per source)
- ✅ Standard libraries (pandas, sklearn, yfinance)
- ✅ Single pipeline class (~600 lines, manageable)
- ✅ Clear data flow (Bronze → Silver → Gold)

---

## 📝 Action Items

### Immediate (This Week)
- [x] Fix Series-to-SQLAlchemy bug
- [x] Add RabbitMQ predictions publishing
- [x] Create `/forecasts/homepage` API endpoint
- [ ] Test end-to-end flow with frontend
- [ ] Upload artifacts to Hetzner S3

### Short-term (Next 2 Weeks)
- [ ] Add APK-Inform parser
- [ ] Add ProAgro parser
- [ ] Store currency rates in silver layer
- [ ] Set up cron job for daily runs
- [ ] Fix Delta Lake compatibility

### Long-term (Next Month)
- [ ] Implement Airflow DAG
- [ ] Add model performance tracking
- [ ] Create monitoring dashboard (Grafana)
- [ ] Implement A/B testing framework

---

## 🎯 Success Criteria

✅ **Pipeline Stability**: Zero crashes, 100% successful runs  
✅ **Data Quality**: <5% missing values in silver layer  
✅ **Forecast Accuracy**: Mean Absolute Error <10% for 1-day predictions  
✅ **API Performance**: <500ms response time for `/forecasts/homepage`  
✅ **Integration**: Forecasts visible on frontend homepage  
✅ **Notifications**: Telegram messages sent for major price changes  

---

## 📚 References

- [Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)
- [Delta Lake Documentation](https://docs.delta.io/)
- [Yahoo Finance API](https://pypi.org/project/yfinance/)
- [Linear Regression](https://scikit-learn.org/stable/modules/linear_model.html)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [RabbitMQ Patterns](https://www.rabbitmq.com/getstarted.html)

---

**Last Updated**: January 9, 2026  
**Next Review**: January 23, 2026
