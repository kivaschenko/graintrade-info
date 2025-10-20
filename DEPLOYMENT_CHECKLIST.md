# ✅ Deployment Checklist - Free Geocoding

## Pre-Deployment

- [ ] Backup existing database
  ```bash
  docker exec graintrade-postgres pg_dump -U user graintrade_db > backup_$(date +%Y%m%d).sql
  ```

- [ ] Review all changes in CHANGES_SUMMARY.md
- [ ] Test geocoding service locally
  ```bash
  python scripts/test_geocoding.py
  ```

## Backend Deployment

### 1. Dependencies
- [ ] Install aiohttp
  ```bash
  cd backend
  poetry add aiohttp
  # or
  pip install aiohttp
  ```

- [ ] Verify dependencies installed
  ```bash
  poetry show | grep aiohttp
  # or
  pip list | grep aiohttp
  ```

### 2. Code Changes
- [ ] Pull latest code with geocoding changes
- [ ] Verify new files exist:
  - [ ] `backend/app/service_layer/geocoding_service.py`
  - [ ] Updated `backend/app/schemas.py`
  - [ ] Updated `backend/app/models/items_model.py`
  - [ ] Updated `backend/app/routers/item_routers.py`

### 3. Database Migration
- [ ] **Option A**: Run migration on existing database
  ```bash
  docker exec -it graintrade-postgres psql -U user -d db \
    -f /docker-entrypoint-initdb.d/migration_add_address.sql
  ```

- [ ] **Option B**: Rebuild database (⚠️ DATA LOSS!)
  ```bash
  docker-compose down -v postgres
  docker-compose up -d postgres
  ```

- [ ] Verify database changes
  ```bash
  docker exec -it graintrade-postgres psql -U user -d db \
    -c "\d items"
  ```
  Should show:
  - `address` VARCHAR(300) column
  - `latitude` NUMERIC (nullable)
  - `longitude` NUMERIC (nullable)

### 4. Restart Backend
- [ ] Restart backend service
  ```bash
  docker-compose restart backend
  ```

- [ ] Check backend logs for errors
  ```bash
  docker-compose logs -f backend | head -50
  ```

- [ ] Verify backend is healthy
  ```bash
  curl http://localhost:8000/docs
  ```

## Frontend Deployment

### 1. Code Changes
- [ ] Replace ItemForm component
  ```bash
  cd frontend/src/components
  cp ItemForm.vue ItemForm_old.vue.backup
  cp ItemForm_new.vue ItemForm.vue
  ```

- [ ] Verify file replaced
  ```bash
  grep -n "address" frontend/src/components/ItemForm.vue
  ```
  Should show address field in template

### 2. Translations
- [ ] Add translations from `i18n_translations_addon.txt` to:
  - [ ] `frontend/src/locales/en.json`
  - [ ] `frontend/src/locales/ua.json`

- [ ] Verify translations added
  ```bash
  grep "address" frontend/src/locales/en.json
  grep "address" frontend/src/locales/ua.json
  ```

### 3. Build & Deploy
- [ ] Build frontend
  ```bash
  cd frontend
  npm run build
  ```

- [ ] Check for build errors
  ```bash
  echo $?  # Should be 0
  ```

- [ ] Restart frontend service
  ```bash
  docker-compose restart frontend
  ```

- [ ] Verify frontend is accessible
  ```bash
  curl http://localhost:3000
  ```

## Testing

### 1. Unit Tests
- [ ] Test geocoding service
  ```bash
  python scripts/test_geocoding.py
  ```

- [ ] Verify successful geocoding
  ```
  Expected output:
  ✅ Success! Latitude: 50.4501, Longitude: 30.5234
  ```

### 2. Integration Tests
- [ ] Test item creation via UI
  - [ ] Navigate to create item page
  - [ ] Fill out form with address
  - [ ] Submit form
  - [ ] Verify item created
  - [ ] Check coordinates populated

- [ ] Test item creation via API
  ```bash
  curl -X POST http://localhost:8000/items \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "category_id": 1,
      "offer_type": "sell",
      "title": "Test Wheat",
      "price": 250,
      "currency": "USD",
      "amount": 1000,
      "measure": "metric ton",
      "terms_delivery": "FOB",
      "address": "Kyiv, Ukraine",
      "country": "Ukraine"
    }'
  ```

- [ ] Verify response contains coordinates
  ```json
  {
    "latitude": 50.4501,
    "longitude": 30.5234,
    ...
  }
  ```

### 3. Map Display
- [ ] Navigate to items map view
- [ ] Verify new items appear on map
- [ ] Click on marker
- [ ] Verify item details show address

### 4. Backward Compatibility
- [ ] Test old API with coordinates
  ```bash
  curl -X POST http://localhost:8000/items \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "category_id": 1,
      "latitude": 50.0,
      "longitude": 30.0,
      ...
    }'
  ```

- [ ] Verify item created without geocoding

### 5. Error Handling
- [ ] Test with invalid address
  ```bash
  # Should create item but without coordinates
  ```

- [ ] Test with empty address
  ```bash
  # Should fail validation or create without geocoding
  ```

## Monitoring

### 1. Logs
- [ ] Monitor backend logs for geocoding activity
  ```bash
  docker-compose logs -f backend | grep geocoding
  ```

- [ ] Check for rate limit warnings
  ```bash
  docker-compose logs backend | grep "rate limit"
  ```

### 2. Database
- [ ] Query recent items
  ```sql
  SELECT id, title, address, latitude, longitude 
  FROM items 
  ORDER BY created_at DESC 
  LIMIT 10;
  ```

- [ ] Verify address and coordinates populated

### 3. Performance
- [ ] Monitor geocoding response times
  ```bash
  docker-compose logs backend | grep "Geocoded coordinates"
  ```

- [ ] Check Nominatim API status
  ```bash
  curl -I https://nominatim.openstreetmap.org/
  ```

## Post-Deployment

### 1. Documentation
- [ ] Update user documentation
- [ ] Add help text for address field
- [ ] Document CSV import format

### 2. Cleanup
- [ ] Remove old ItemForm backup if not needed
  ```bash
  rm frontend/src/components/ItemForm_old.vue.backup
  ```

- [ ] Archive old database backup
  ```bash
  gzip backup_*.sql
  ```

### 3. Monitoring Setup
- [ ] Set up alerts for geocoding failures
- [ ] Monitor Nominatim rate limit compliance
- [ ] Track geocoding success rate

## Rollback Plan

If issues occur:

### 1. Database Rollback
```bash
# Restore from backup
docker exec -i graintrade-postgres psql -U user graintrade_db < backup_YYYYMMDD.sql
```

### 2. Code Rollback
```bash
# Restore old ItemForm
cd frontend/src/components
cp ItemForm_old.vue.backup ItemForm.vue

# Rebuild frontend
cd ../..
npm run build
docker-compose restart frontend
```

### 3. Backend Rollback
```bash
# Checkout previous version
git checkout <previous-commit>

# Restart backend
docker-compose restart backend
```

## Success Criteria

- ✅ All tests pass
- ✅ Items created with addresses show on map
- ✅ Geocoding works for various address formats
- ✅ No errors in logs
- ✅ Old API still works
- ✅ Performance acceptable (<2s for geocoding)
- ✅ Users can create items successfully

## Support Checklist

- [ ] Document known issues
- [ ] Create FAQ for common problems
- [ ] Set up monitoring alerts
- [ ] Update runbook with troubleshooting steps

## Notes

**Date Deployed**: _______________

**Deployed By**: _______________

**Database Backup Location**: _______________

**Issues Encountered**: 

_________________________________________________________________

_________________________________________________________________

**Resolution**:

_________________________________________________________________

_________________________________________________________________

---

**Status**: 
- [ ] ✅ Deployment Successful
- [ ] ⚠️ Partial Success (specify issues)
- [ ] ❌ Rollback Required

**Sign-off**: _______________
