# Parser Configuration System - Implementation Checklist

## Phase 1: Core Files (Already Created)

### Documentation
- [x] `PARSER_CONFIG_GUIDE.md` - Comprehensive guide with examples
- [x] `PARSER_USAGE_EXAMPLES.md` - Practical API and code examples  
- [x] `PARSER_IMPLEMENTATION_GUIDE.md` - Architecture and integration details
- [x] `PARSER_QUICK_REFERENCE.md` - Quick lookup and commands

### Code Files
- [x] `app/services/parser_factory.py` - Factory for parser instantiation
- [x] `app/services/config_validator.py` - Configuration validation
- [x] `app/routers/ingestion_router_enhanced.py` - Enhanced ingestion router

### Existing Files (Already Have Config Support)
- [x] `app/models/data_source_model.py` - Has `config` JSON column
- [x] `app/schemas/data_source_schema.py` - Includes config field

---

## Phase 2: Integration Steps

### 1. Add Parser Factory to Imports
```python
# In app/__init__.py or app/services/__init__.py
from app.services.parser_factory import ParserFactory
from app.services.config_validator import ConfigValidator
```

### 2. Merge Enhanced Router into Existing Router
```bash
# Option A: Replace ingestion_router.py with ingestion_router_enhanced.py
cp app/routers/ingestion_router_enhanced.py app/routers/ingestion_router.py

# Option B: Merge functions manually into existing router
# - Copy run_ingestion_job_with_parser function
# - Copy get_supported_parsers endpoint
# - Update imports
```

### 3. Update Router Imports
```python
# In app/main.py
from app.routers import ingestion_router
from app.services.parser_factory import ParserFactory
from app.services.config_validator import ConfigValidator
```

### 4. Register Parsers (Optional - For Clarity)
```python
# In app/services/parser_factory.py or app/__init__.py
from app.parser_services import (
    APKInformParser,
    InvestingComParser,
    TripoliLandParser,
    YFinanceParser,
    CurrencyParser,
    GraintradeComuaParser,
)

# Auto-register all parsers
ParserFactory.register("apk_inform", APKInformParser)
ParserFactory.register("investing_com", InvestingComParser)
# ... etc
```

---

## Phase 3: Testing

### Unit Tests

#### Test Parser Factory
```python
# tests/test_parser_factory.py
import pytest
from app.models import DataSource
from app.services.parser_factory import ParserFactory

def test_create_apk_inform_parser():
    ds = DataSource(
        name="Test",
        config={"parser_type": "apk_inform", "regions": ["Odesa"]}
    )
    parser = ParserFactory.create_parser(ds)
    assert parser is not None
    assert hasattr(parser, 'parse')

def test_unknown_parser_type():
    ds = DataSource(
        name="Test",
        config={"parser_type": "unknown"}
    )
    with pytest.raises(ValueError):
        ParserFactory.create_parser(ds)
```

#### Test Config Validator
```python
# tests/test_config_validator.py
from app.services.config_validator import ConfigValidator

def test_valid_apk_inform_config():
    config = {
        "parser_type": "apk_inform",
        "regions": ["Odesa"]
    }
    is_valid, errors = ConfigValidator.validate(config)
    assert is_valid
    assert len(errors) == 0

def test_invalid_yfinance_config():
    config = {
        "parser_type": "yfinance"
        # Missing required 'tickers'
    }
    is_valid, errors = ConfigValidator.validate(config)
    assert not is_valid
    assert "tickers" in str(errors)
```

### Integration Tests

#### Test Ingestion Endpoint
```python
# tests/test_ingestion_router.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_parser_source():
    response = client.post("/data-sources", json={
        "name": "Test APK",
        "source_type": "web_scraping",
        "config": {"parser_type": "apk_inform"}
    })
    assert response.status_code == 201
    assert response.json()["id"] == 1

def test_start_ingestion_job():
    # First register
    client.post("/data-sources", json={
        "name": "Test", "config": {"parser_type": "apk_inform"}
    })
    
    # Then ingest
    response = client.post("/ingestion/start", json={
        "data_source_id": 1,
        "layer": "bronze"
    })
    assert response.status_code == 202
    assert "job_id" in response.json()
```

---

## Phase 4: Deployment

### 1. Database Migrations
```bash
# Verify data_sources table has config column
alembic current

# If missing, create migration:
alembic revision --autogenerate -m "Add config to data_sources"
alembic upgrade head
```

### 2. Test New Endpoints
```bash
# Check health
curl http://localhost:8001/health

# List parsers
curl http://localhost:8001/ingestion/parsers

# Try registering a data source
curl -X POST http://localhost:8001/data-sources \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "config": {"parser_type": "apk_inform"}}'
```

### 3. Monitor Startup Logs
```bash
# Look for:
# - "Registered parser: apk_inform"
# - "Parser registry has X parsers"
# - No import errors
```

---

## Phase 5: Validation Checklist

- [ ] Can register DataSource with config JSON
- [ ] Can validate config via ConfigValidator
- [ ] Can create parser via ParserFactory
- [ ] Can trigger ingestion job via API
- [ ] IngestionLog records jobs correctly
- [ ] Parser executes and returns data
- [ ] Results stored in bronze layer
- [ ] Job status updates properly
- [ ] Error handling works (invalid configs, missing data, etc.)
- [ ] All parsers registered and functional

---

## Phase 6: Documentation & Training

### For Developers
- [ ] Share PARSER_IMPLEMENTATION_GUIDE.md
- [ ] Review ParserFactory code
- [ ] Understand ConfigValidator rules
- [ ] Practice adding a new parser

### For Operations
- [ ] Share PARSER_USAGE_EXAMPLES.md
- [ ] Create data sources for each parser
- [ ] Set up monitoring dashboard
- [ ] Document runbooks for troubleshooting

### For Stakeholders
- [ ] Share PARSER_CONFIG_GUIDE.md overview
- [ ] Demonstrate API workflow
- [ ] Show monitoring capabilities

---

## Phase 7: Rollout Plan

### Week 1: Setup & Testing
- [ ] Merge code into main branch
- [ ] Run all unit tests
- [ ] Deploy to staging environment
- [ ] Run integration tests
- [ ] Get code review approval

### Week 2: Validation & Documentation
- [ ] Test with real data sources
- [ ] Validate all parser types work
- [ ] Create final documentation
- [ ] Train team

### Week 3: Production Deployment
- [ ] Deploy to production
- [ ] Migrate existing data sources (if needed)
- [ ] Monitor logs for issues
- [ ] Support team during transition

### Week 4: Optimization & Monitoring
- [ ] Analyze performance metrics
- [ ] Optimize slow parsers
- [ ] Setup alerting for failures
- [ ] Document lessons learned

---

## Common Issues & Solutions

### Issue: "Installed module not found"
**Cause:** Parser class not imported in factory
**Solution:** Add import in `parser_factory.py`
```python
from app.parser_services.myparser import MyParser
```

### Issue: "Unknown parser type"
**Cause:** Parser not registered in PARSER_REGISTRY
**Solution:** Add to registry in ParserFactory
```python
PARSER_REGISTRY = {
    "myparser": MyParser,  # Add this
}
```

### Issue: "Config validation failed"
**Cause:** Required field missing in config
**Solution:** Check ConfigValidator.REQUIRED_FIELDS for parser type

### Issue: "Parser returned no data"
**Cause:** Website down, bad parameters, or parsing logic issue
**Solution:** 
1. Check logs for specific error
2. Verify website accessibility
3. Test parser in isolation

### Issue: "Job stuck in 'running' state"
**Cause:** Parser hanging or infinite loop
**Solution:** 
1. Check logs for last message
2. Kill stuck process
3. Fix parser logic or timeout

---

## Monitoring & Metrics

### Key Metrics to Track
```sql
-- Success rate by parser
SELECT 
    parser_type,
    COUNT(*) as total,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
    ROUND(100.0 * SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM ingestion_logs il
JOIN data_sources ds ON il.data_source_id = ds.id
WHERE ds.config->>'parser_type' IS NOT NULL
GROUP BY parser_type;

-- Average execution time
SELECT 
    ds.name,
    AVG(EXTRACT(EPOCH FROM (il.completed_at - il.started_at))) as avg_duration
FROM ingestion_logs il
JOIN data_sources ds ON il.data_source_id = ds.id
WHERE il.status = 'completed'
GROUP BY ds.name;

-- Failed jobs
SELECT 
    ds.name,
    COUNT(*) as failures
FROM ingestion_logs il
JOIN data_sources ds ON il.data_source_id = ds.id
WHERE il.status = 'failed'
GROUP BY ds.name
ORDER BY failures DESC;
```

### Set Up Alerts
```python
# In monitoring/alerts.py
- Alert if parser success rate < 95%
- Alert if average execution time increases by 50%
- Alert if any parser fails 3 times in a row
- Alert if config validation errors > 10 per day
```

---

## Rollback Plan

If something goes wrong:

```bash
# 1. Revert code
git revert <commit>

# 2. Stop ingestion jobs
UPDATE ingestion_logs SET status = 'failed' 
WHERE status IN ('started', 'running');

# 3. Disable all parser sources
UPDATE data_sources SET is_active = FALSE 
WHERE config->>'parser_type' IS NOT NULL;

# 4. Verify traditional ingestion still works
# Test with non-parser data sources

# 5. Investigation
# - Check logs
# - Identify issue
# - Fix and test
# - Redeploy
```

---

## Success Criteria

- ✅ All parsers registered and functional
- ✅ Config validation catches errors
- ✅ ParserFactory creates parsers correctly
- ✅ Ingestion router works with parsers
- ✅ IngestionLog tracks all jobs
- ✅ Parser success rate > 95%
- ✅ Average execution time acceptable
- ✅ No regressions in existing functionality
- ✅ Team trained and confident
- ✅ Monitoring alerts configured

---

## Next Steps

1. **Today:** Review all documentation
2. **Tomorrow:** Review code files
3. **Day 3:** Merge into staging branch
4. **Day 4:** Run tests
5. **Day 5:** Deploy to staging
6. **Day 6:** Validation
7. **Day 7:** Production deployment

---

## Contact & Support

For questions about:
- **Architecture** → See PARSER_IMPLEMENTATION_GUIDE.md
- **API Usage** → See PARSER_USAGE_EXAMPLES.md
- **Configuration** → See PARSER_CONFIG_GUIDE.md
- **Quick Help** → See PARSER_QUICK_REFERENCE.md

---

## Sign Off

- [ ] Architecture reviewed
- [ ] Code reviewed
- [ ] Tests passing
- [ ] Deployment approved
- [ ] Team trained
- [ ] Go-live approval
- [ ] Post-go-live monitoring confirmed

**Date:** __________
**Approved by:** __________
