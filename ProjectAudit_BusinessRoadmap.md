# GrainTrade Info – Project Audit & Business Growth Roadmap

**Audit Date:** November 18, 2025  
**Objective (90 days):** Reach first $2–3K monthly recurring revenue (MRR) by converting existing technical assets into paid value (premium data, alerts, API) while laying scalable foundations (instrumentation + cloud readiness).

---

## 1. Executive Summary

The platform already runs a modern microservices stack (FastAPI services + Vue.js SPA + ancillary services for chat, notifications, landing, parsers, cron). A subscription layer and premium OpenAPI filtering logic exist, indicating early monetization intent, but no integrated pricing, tracking, or payment conversion funnel is visibly enforced yet. Core opportunity: productize existing data, geospatial capabilities, and alerting into tiered offerings and B2B analytics within 3 months.

### Current Observed State
- Stack: FastAPI (backend, chat-room, notifications, landing), Vue 3 frontend, PostgreSQL, Redis, RabbitMQ, Prometheus/Grafana, Apache reverse proxy, Docker Compose.
- Hosting: Hetzner AX41-NVMe dedicated (€39/mo) – powerful but under‑utilized.
- Monetization: Subscription models implied (tarif/subscription models + premium OpenAPI filter) but not clearly exposed in frontend funnel; payment service files present (nowpayments / crypto) but revenue = $0.
- Instrumentation: Prometheus configured; application endpoints do not expose metrics yet (Prometheus expects /metrics paths which seem missing in code). No GA/Clarity/Amplitude integration found.
- Tests: Limited unit + subscription/tarif tests; modest breadth (needs coverage expansion for payments, security, geocoding, performance). E2E folder exists but not fully leveraged.
- Security: Apache config with proactive blocking & headers; JWT auth + bcrypt; Redis rate limiting mentioned in README but not confirmed in code paths.

### Key Gaps (Impact vs Effort)
1. No active analytics/user funnel tracking (blocks data-driven iteration).
2. Premium value not clearly packaged (pricing page, upgrade CTAs, in-app upsell triggers missing).
3. Metrics endpoints mismatch (Prometheus configured but services not exporting domain metrics → blind spots for latency/business KPIs).
4. Payment integration not fully surfaced (frontend lacks polished subscription purchase flow & billing status pages).
5. Data export / historical analytics potential unused in marketing narrative.
6. No structured activation loop (user signs up → config alerts → sees ROI quickly).
7. Infrastructure static (no auto-scaling / secrets centralization) – acceptable now but need future migration path.
8. Limited SEO/content engine for organic acquisition.

### Strategic Thrust (Next 90 Days)
Monetize fastest path assets: (a) Premium Data & Exports, (b) Alerts & Geospatial filters, (c) Paid API access, (d) Sponsored corporate listings. Layer instrumentation & feedback loop. Pilot B2B analytics (market trend mini dashboards) by Month 3.

---

## International GTM Addendum (UA → EN/Global)

### Recommendation In Brief
- Keep Ukraine as the supply-side nucleus (data, listings, local network). Add English as the demand-side interface targeting global B2B (traders, importers, logistics, feed mills). Do not fully pivot to US B2C; instead, sell Black Sea/CEE intelligence and listings access to global buyers in English.

### Positioning
- Unique edge: granular geospatial listings, Black Sea/CEE context, and fresh data feeds that many large-audience competitors lack in quality. Package this as “Black Sea Agricultural Market Intelligence & Listings API.”

### Language & SEO
- Domains: `graintrade.info` (UA default), `en.graintrade.info` (EN default). Add `hreflang` and canonical tags; auto-detect browser language on first visit. Maintain UA SEO; create EN landing pages for “Ukrainian grain export data”, “Black Sea port activity”, “Ukraine rail logistics”, “feed wheat prices Ukraine”.

### ICPs (Prioritized)
- Tier 1: Global grain traders/brokers; EU importers; Turkish/Egyptian buyers; logistics firms operating in Black Sea.
- Tier 2: Feed mills/procurement teams (CEE, MENA); maritime analytics firms wanting API enrichment.
- Tier 3: Market newsletters/data platforms seeking embedded widgets.

### Offers by Segment
- Buyers/Traders: premium alerts (new offers in target regions/specs), unlimited exports, historical trends, API access; concierge sourcing (add-on).
- Logistics: rail/port throughput indicators, route/region alerts, sponsored placement to reach sellers.
- Data Platforms: API subscription with SLA + widgets (map/listing embed) and revenue-share referrals.

### Go-To-Market Channels (Low-Cost First)
- Account-based outreach: identify 50 target firms; LinkedIn + email sequence (3 touches) offering a 14-day premium trial and sample CSV/API.
- Telegram partnerships: sponsored posts in top UA/CEE agri/logistics channels; launch an English Telegram bot with daily digest to collect leads.
- Content engine: 1 weekly EN post with charts on Black Sea exports, port status, rail bottlenecks (gate full CSV to capture emails).
- PR/communities: Post in commodity/agribusiness Slack/Discord/Reddit groups with data snippets; invite to free webinar demo monthly.

### Pricing & Packaging (EN Site)
- Keep UA-friendly pricing on UA site; publish USD pricing on EN site. Use the tiers defined in Section 3; emphasize API and alerts in copy.
- Include “Book a demo” CTA and annual plans (-15%). Offer invoice/wire for Business+.

### Product Adjustments
- EN onboarding wizard (interests/regions/thresholds) to hit “value in 48h”.
- Stripe (USD) + invoices; company profiles & VAT fields. Downloadable sample datasets and live API sandbox key (rate-limited).
- Case studies: 2 short write-ups showing time saved and deal discovery value.

### KPIs to Validate Strategy (60–90 Days)
- 20 demo calls booked (EN site), 10 trials started, 3–5 paid conversions (Premium/Business/API).
- Alert engagement rate > 20%, export-to-upgrade conversion ≥ 8%.
- CAC for B2B ≤ $400; LTV target ≥ $1,000.

### 30-60-90 Plan (EN/Global)
- 0–30 days: EN landing + pricing + demo booking; Telegram bot (EN) digest; 2 EN case studies; ABM list of 50 target companies; start outreach; run 1 webinar.
- 31–60 days: Ship alerts + exports in EN funnels; publish 4 weekly EN insights; partner posts in 3 Telegram channels; onboard 3 design partners on API.
- 61–90 days: Sponsored listings rollout; refine API quotas; 2 paid pilots; decide on scaling Azure staging if ≥30 paid subs or ≥5 API clients.

### Why Not Full US Pivot?
- Mature US incumbents, high CAC, and heavy data expectations. Your near-term moat is Black Sea/CEE expertise delivered in English to global buyers. Prove B2B value first; expand later if economics justify.

---

## 2. Architecture Assessment

### High-Level Microservice Topology
```
frontend (Vue SPA) → Apache reverse proxy →
  backend (FastAPI core API)    : auth, items, categories, payments, subscriptions
  chat-room (FastAPI WS)        : real-time messaging
  notifications (FastAPI)       : email/Telegram/SMS (?) dispatch
  landing-service (Flask)       : marketing pages (simpler deploy)
Supporting: PostgreSQL, Redis (cache/session/rate-limit), RabbitMQ (event bus), Prometheus+Grafana (monitoring), cron_services & parsers (data ingestion/update).
```

### Strengths
- Modular service separation enabling targeted scaling and isolation.
- FastAPI + async stack → efficient I/O for real-time + data endpoints.
- Existing subscription & premium OpenAPI filtering logic (accelerates monetization).
- Geospatial capabilities (Mapbox integration) – differentiator for location-based commodity listings.
- Dockerized deployment with health checks → manageable CI/CD improvements.
- Security-conscious Apache configuration & CORS explicit origins.

### Weaknesses / Technical Debt
- Metrics endpoints missing (Prometheus config expects /metrics) → lack of latency / throughput / business counters.
- Connection pool static (asyncpg min/max size 10; adjust dynamically or reduce for low load & add instrumentation around failures/timeouts).
- Redis connection pool creation is simplistic; consider robust health checks & retry/backoff.
- Payment & subscription logic scattered (service_layer + routers) – needs consolidation for clearer upgrade flow + entitlement enforcement (e.g. scope gating across endpoints).
- Limited automated test breadth (payments, security, map/geocoding, rate limits not covered).
- No feature flag system for controlled rollout (could introduce simple environment-based toggle or a flags table in Redis/Postgres).
- Secrets management via .env on disk; should transition to a vault or Azure Key Vault later.
- Single dedicated server = SPOF (lack of rolling deployment, no blue/green strategy).

### Suggested Architecture Enhancements (Incremental)
1. Add a lightweight metrics middleware (request latency histogram, request count, error count, subscription tier usage) → expose at /metrics.
2. Centralize subscription entitlement check decorator (DRY enforcement before endpoints, unify scope names).
3. Introduce a Business Events emitter (e.g., publish “ITEM_CREATED”, “SUBSCRIPTION_UPGRADED”, “ALERT_TRIGGERED”) into RabbitMQ → drive analytics & future billing metrics.
4. Implement structured logging (JSON) with correlation IDs (request id) for downstream aggregation.
5. Add idempotency keys for payment webhook handling (reduce double-charging risk).

---

## 3. Monetization Strategy (Prioritized)

| Tier / Stream | Description | Launch Order | 90d MRR Potential |
|---------------|-------------|--------------|------------------|
| Premium Subscription | Unlock exports (CSV/Excel), historical price trend charts, configurable alerts, map layer filters | Weeks 2–3 | $700–1,200 |
| Public API Paid Calls | Rate-limited commodity/item/geo endpoints (API keys, usage dashboard) | Weeks 4–6 | $600–1,000 |
| Sponsored / Featured Listings | Highlight seller profiles & items in search/map (limited slots) | Weeks 6–8 | $300–500 |
| Alert Credits (Add-On) | Pay-per volume of email/Telegram/SMS alerts beyond plan quota | Weeks 7–9 | $200–400 |
| B2B Analytics Mini Dashboards | Aggregated regional supply, velocity, pricing indices | Weeks 9–12 | $300–600 |
| Seasonal Market Reports | PDF + interactive (upsell) | Week 10+ | $200–300 |

### Pricing Draft (Iteration Required)
```
Free:    Basic browse, limited map zoom, 5 item views/day, no exports.
Premium: $29/mo  Unlimited item views, exports, 50 alerts/mo, historical charts (30d), premium docs subset.
Business: $99/mo  All Premium + 300 alerts/mo, advanced filters, 1 sponsored slot credit, historical (180d).
Enterprise: Custom  SLA, dedicated analytics feed, bulk API, custom indices.
API Only Starter: $49/mo  1,000 calls.
API Growth:       $149/mo 10,000 calls.
API Scale:        $499/mo 100,000 calls.
Alert Overages: $5 per extra 100 alerts (email/Telegram bundle).
Sponsored Listing: $129/mo per slot (cap slots to create scarcity; rotate by category/region).
Report (single): $99 – $199; Report subscription addon: +$79/mo.
```

### Fastest Activation Loop
1. User registers → immediate guided setup wizard (select commodity interests + regions + alert thresholds).
2. Trial Premium 7 days (full features, watermark on exports) → daily value email (“New offers matched your filters”).
3. After 3 meaningful alerts or one export, trigger upgrade modal (value proven before paywall).
4. At trial end → downgrade preview (lost features UI) + limited alert throttling → convert.

### Immediate Implementable (Weeks 1–2)
- Define entitlements matrix (features vs tier) in a single JSON + code constants.
- Build export endpoint (CSV/Excel streaming) using existing models & filters.
- Implement alert scheduling (cron_services) with per-user queue & usage counters in Redis.
- Add upgrade CTA bars in frontend (top + item detail + map overlay when locked features clicked).

---

## 4. 90-Day Execution Roadmap (By Weeks)

### Weeks 1–2 (Foundation & Instrumentation)
- Implement GA4 + Microsoft Clarity + backend custom metrics (/metrics).
- Entitlements matrix & subscription scope enforcement wrapper.
- Payment flow polish (frontend purchase → webhook confirmation → user scope upgrade).
- Basic export & historical data endpoint MVP.
- SEO quick wins: sitemap.xml, canonical tags, meta descriptions, structured data for item listings (Product / Offer schema).

### Weeks 3–4 (Premium Feature Depth & API Launch Prep)
- Alert engine (create/edit thresholds, commodity-region pairing, daily digest + instantaneous triggers).
- API key issuance & management (create/revoke, show usage counts).
- Rate limiting (token bucket using Redis, tier-based quotas) + usage dashboard endpoint.
- Documentation pages (public vs premium) – already partial filter logic present; finalize & publish.

### Weeks 5–6 (API Monetization & Reliability)
- Launch API tiers + billing integration (Stripe or NowPayments bridging card/crypto).
- Add sponsored listing schema & highlight rendering in search/map.
- Enhanced logging + anomaly alerting (error rate, failed payments, dropped alerts).
- Begin Azure migration staging environment build (Container Apps & PostgreSQL flexible server) – dual-run low traffic features to validate.

### Weeks 7–8 (Growth Features & Azure Go-Live)
- Finalize Azure cutover (DNS + SSL) – maintain Hetzner as rollback for 7 days.
- Inject B2B mini dashboard (regional supply index, price movement sparkline) for Business tier.
- Launch sponsored listing management UI (purchase, slot assignment, analytics impressions/clicks).
- Email nurture flow (trial day 2 value highlight, day 5 urgency, day 7 conversion).

### Weeks 9–12 (Optimization & Expansion)
- Performance tuning (DB pool sizing dynamic, caching hot queries, map tile optimization).
- Report generation pipeline (monthly aggregated metrics export to PDF, store in Blob Storage).
- Alert overage billing + churn prevention triggers (usage drop emails).
- A/B tests (pricing page CTA wording, upgrade modal variants).

---

## 5. Azure Migration Evaluation

### Service Mapping
| Current | Azure Target (Phase 1) | Phase 2 (Scale) |
|---------|-----------------------|-----------------|
| FastAPI services | Azure Container Apps (revision autoscale) | AKS (if >3–5 containers need complex orchestration) |
| PostgreSQL | Azure Database for PostgreSQL Flexible (Basic) | General Purpose tier |
| Redis | Azure Cache for Redis Basic C0 | Standard C1/C2 |
| RabbitMQ | Azure Service Bus (Queues/Topics) or Managed RabbitMQ (Marketplace) | Service Bus Premium / Event Hub (if streaming) |
| Static SPA (frontend) | Azure Static Web Apps or Blob + CDN | Azure Front Door + CDN |
| Landing Flask | Azure App Service (B1) | Fold into Container Apps |
| File exports / reports | Azure Blob Storage (Hot) | Archive tier for historical |
| Monitoring | Azure Monitor + Log Analytics + Managed Grafana | Add Application Insights + Cost alerts |
| Secrets (.env) | Azure Key Vault | Key Vault + Managed Identity |

### Indicative Monthly Cost (Early Load)
```
Container Apps (4 small revisions, low CPU):   $20–28
PostgreSQL Flexible Basic (1 vCore + 32GB):    $13–18
Redis Cache Basic C0:                          $15–17
Service Bus Basic (low ops):                   $5–10
Blob Storage (reports/exports <25GB):          $2–5
Log Analytics + Monitor (conservative):        $10–15
Static Web App (Free tier possible early)      $0–9
Key Vault (low secrets ops):                   $2–4
---------------------------------------------
Estimated:                                     $70–100 USD (~€65–95)
```
Comparable to current Hetzner when factoring future scale safety, managed backups, autoscaling, and observability.

### Migration Phasing
1. Stand up Azure staging (Container Apps + Postgres replica restore) → shadow traffic tests.
2. Introduce dual-write (optional) for critical data changes for 3–5 days.
3. Cut DNS (Traffic Manager / Front Door) with low TTL rollback plan.
4. Post-cut verification: payments, alerts, websockets (chat), latency baseline.
5. Decommission Hetzner only after 14-day stability window.

### Risks & Mitigations
- Latency variance: Use regional placement + CDN for static assets.
- Message compatibility (RabbitMQ → Service Bus): Abstract broker interface & test event ordering; keep RabbitMQ initially if migration risk too high.
- Cost creep: Set budget alerts + daily anomaly script (cost > threshold → notify).

---

## 6. Critical Technical Improvements (Prioritized)
1. Metrics Middleware + /metrics endpoint (requests_total, latency_seconds histogram, active_subscriptions gauge, alerts_sent_total, export_requests_total).
2. Unified entitlement decorator (prevent scattered subscription checks; improves maintainability & auditability).
3. Payment webhook idempotency (persist processed event IDs; reject duplicates).
4. Export service (streaming large CSV using async generator + compression) with usage counters per subscription.
5. Alert service re-architecture: schedule table + Redis queue + worker in cron_services; guarantee at-least-once delivery; per-user daily usage cap enforcement.
6. Security enhancements: rate limit login/password recovery; rotate JWT secret through Key Vault later; add content-security-policy tune for frontend.
7. Automated tests expansion: payments (success/failure), subscription downgrade after expiry, alert generation logic, map filter queries performance.

---

## 7. KPI & Analytics Framework

### Product KPIs
- Activation Rate (users completing alert setup within 48h).
- Export Conversion Rate (exports leading to upgrades / trials).
- Alert Engagement (CTR on alert emails/Telegram messages).
- API Usage Distribution (calls per tier vs quota).
- Sponsored Listing CTR & impressions.

### Engineering / Reliability KPIs
- p95 backend latency, error rate (%) per service.
- Failed payment webhook count (daily).
- Alert dispatch success rate (% delivered vs scheduled).
- Cache hit ratio (Redis), DB slow queries (>200ms).
- Deployment frequency & mean time to recovery (MTTR).

### Instrumentation Implementation Order
Week 1: GA4, Clarity, basic backend request/error counters.
Week 2: Subscription & alert event counters.
Week 3–4: API usage & quota dashboards.
Week 5+: Cost & churn analytics; integrate with Grafana business panels.

---

## 8. Revenue Projection (Conservative)
```
Month 1: 20 Premium trials → 10 conversions @ $29  = $290
          + Early sponsored pilot 2 slots @ $129    = $258
          + Minimal API early adopters (2 @ $49)     = $98
          ----------------------------------------------
          ≈ $646
Month 2: 40 Premium subs (growth/content/alerts)     = $1,160
          6 API clients mixed tiers (~$450 avg)       = $450
          5 Sponsored listings @ $129                 = $645
          Alert overage / reports                     = $150
          ----------------------------------------------
          ≈ $2,405
Month 3: 60 Premium subs                             = $1,740
          10 API clients (avg $110)                   = $1,100
          8 Sponsored listings                        = $1,032
          Reports + B2B dashboards                    = $400
          ----------------------------------------------
          ≈ $4,272 (stretch goal; realistic target $2–3K)
```

---

## 9. Risk Register (Updated)
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Slow adoption of paid tiers | Medium | High | Aggressive trial → value emails → upgrade prompts |
| Alert spam / low relevance | Medium | Medium | User-configurable thresholds + digest option |
| Payment churn / failed renewals | Medium | Medium | Retry logic + dunning emails (days -3, 0, +3) |
| Data quality degradation (parsers fail) | Medium | High | Parser health heartbeat + stale data alerts |
| Migration instability (Azure) | Low | High | Staged shadow run + rollback plan |
| API abuse (quota evasion) | Medium | Medium | Signed request id + rate limit + anomaly detection |

---

## 10. Immediate Action Checklist (Week 1)

[X] Add GA4 + Clarity scripts to frontend (non-premium blocking).

[X] Implement /metrics in backend with Prometheus FastAPI instrumentation.

[ ] Define entitlements JSON + integrate decorator across premium endpoints.

[ ] Add trial flag column to subscription model (expiry timestamp) + auto-downgrade cron.

[ ] Create pricing & features page (static marketing + upgrade CTA).

[ ] Draft email templates: Trial Welcome, Trial Day 3 Value, Trial Expiry.

[ ] Set up Stripe (cards) + NowPayments (crypto) unified callback normalizer.

---

## 11. Recommendations Summary (Top 8)
1. Ship instrumentation + entitlements this week to enable data-driven iteration.
2. Focus on exports & alerts as first “Aha!” monetization levers – low build cost, high perceived value.
3. Avoid early AdSense/affiliate distraction unless traffic baseline proves viable (ads can reduce premium conversions early).
4. Harden payment flow (webhook idempotency, UI clarity, downgrade handling) before broad trials.
5. Launch minimal API monetization after subscription funnel stabilized (avoid splitting attention too early).
6. Start Azure staging early (Week 5) but migrate only after stable monetization signals (≥30 paid subs) to justify ops overhead.
7. Build sponsored listing with scarcity mechanics (limited visible slots) to amplify perceived value.
8. Treat parsers & data freshness as core asset – monitor & surface “last updated” stamps to build trust.

---

## 12. Appendix – Implementation Snippets

### FastAPI Metrics (Example Skeleton)
```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Request, APIRouter

REQ_COUNT = Counter('http_requests_total','Total HTTP requests',['method','path','status'])
LATENCY = Histogram('http_request_duration_seconds','Request latency',['method','path'])

@app.middleware('http')
async def metrics_middleware(request: Request, call_next):
    method = request.method
    path = request.url.path
    with LATENCY.labels(method, path).time():
        response = await call_next(request)
    REQ_COUNT.labels(method, path, response.status_code).inc()
    return response

metrics_router = APIRouter()
@metrics_router.get('/metrics')
def metrics():
    return Response(generate_latest(), media_type='text/plain')
app.include_router(metrics_router)
```

### Entitlements Decorator (Concept)
```python
ENTITLEMENTS = {
  'free': {'exports': False,'alerts': 5,'history_days': 0},
  'premium': {'exports': True,'alerts': 50,'history_days': 30},
  'business': {'exports': True,'alerts': 300,'history_days': 180,'sponsored_slots': 1},
}

def require_feature(feature: str):
  def wrapper(fn):
    async def inner(*args, **kwargs):
      user = await get_current_user()
      tier = user.subscription.scope
      if not ENTITLEMENTS.get(tier, {}).get(feature):
        raise HTTPException(status_code=403, detail=f'{feature} not enabled for tier')
      return await fn(*args, **kwargs)
    return inner
  return wrapper
```

### Export Endpoint Sketch
```python
@router.get('/items/export')
@require_feature('exports')
async def export_items(format: str = 'csv'):
    rows = await items_repo.fetch_for_export()
    def row_iter():
        yield 'id,title,price,lat,lon\n'
        for r in rows:
            yield f"{r.id},{r.title},{r.price},{r.latitude},{r.longitude}\n"
    return StreamingResponse(row_iter(), media_type='text/csv')
```

---

**Document Version:** 2.0  
**Last Updated:** November 18, 2025  
**Next Review:** December 18, 2025

---

## Quick Progress Snapshot (To Keep Visible)

[ ] Instrumentation deployed

[ ] Pricing page live
[ ] Trial funnel active
[ ] Alerts engine MVP
[ ] Export feature live
[ ] API keys issuance
[ ] Sponsored listing schema
[ ] Azure staging environment

Let’s convert technical assets into sustainable recurring revenue. 🚀