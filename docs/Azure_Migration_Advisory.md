# Azure Migration Advisory for graintrade.info

Date: 2025-12-11
Author: Single developer/owner

## Context
- Current hosting: Hetzner AX41-NVMe dedicated server (~40 EUR/month)
- Stack: Local Postgres, Redis, Docker-based services (backend, frontend, parsers, cron, notifications, landing, chat-room), RabbitMQ, monitoring (Grafana/Prometheus), Nginx/Apache
- Ops: Manual setup/config, single-server architecture, low monthly infra cost but higher hands-on maintenance

## Migration Goals
- Reduce manual ops effort and increase reliability (managed services)
- Maintain or improve performance and availability
- Keep monthly costs reasonable for a solo developer
- Align with simple deployment workflows (CI/CD)

## Azure Architecture Options (Solo-friendly)

### Option A: Container-centric (baseline)
- `Azure Container Apps` for app services (backend, parsers, cron, notifications, chat-room, landing)
- `Azure Database for PostgreSQL - Flexible Server` (managed Postgres)
- `Azure Cache for Redis` (managed Redis)
- `Azure Service Bus` or `Azure RabbitMQ via Marketplace` (replace RabbitMQ; Service Bus is native)
- `Azure Monitor` + `Container Insights` + `Log Analytics` (replace Grafana/Prometheus or complement)
- Static assets via `Azure Storage + Azure CDN` or `Static Web Apps` for frontend
- Ingress via Container Apps Environment with built-in HTTP ingress; or `Azure Front Door` for global routing + TLS

Pros: Minimal ops, good scaling knobs, easy per-service deployment. Cons: Multiple managed services increase cost and complexity.

### Option B: Simpler VM-first (intermediate)
- `Azure Virtual Machine` for consolidating multiple containers (similar to Hetzner)
- `Azure Database for PostgreSQL` managed; optional `Azure Cache for Redis` managed
- Keep RabbitMQ on the VM or move to Service Bus
- Use `Azure Backup`/`Update Management`, `Azure Monitor` for observability

Pros: Lower migration friction and cost; familiar ops; can incrementally adopt managed services later. Cons: Still VM ops overhead, but with Azure guardrails.

### Option C: Kubernetes (AKS)
- `Azure Kubernetes Service` for all services
- Managed Postgres/Redis
- Ingress via NGINX or AGIC; `Azure Monitor` for observability

Pros: Powerful, scalable; Cons: Overkill for a solo operator, higher complexity and cost.

## Cost Ballpark (EUR/month, modest usage)
- Hetzner: ~40 EUR (current)

Option A (Container Apps + Managed DB/Cache):
- Container Apps: 10–40 EUR (very app-usage dependent; may be higher with sustained CPU)
- Postgres Flexible Server: 25–80 EUR (small–medium SKU)
- Cache for Redis: 15–60 EUR (Basic/Standard small)
- Service Bus (basic/standard): 5–25 EUR
- Log Analytics + Monitor: 5–20 EUR
- Storage + CDN/Static Web Apps: 2–10 EUR
- Total typical: ~60–200+ EUR depending on load and SKUs

Option B (VM + managed DB/Cache):
- VM (B-series/D-series small): 20–60 EUR (spot can be cheaper but interruptible)
- Postgres Flexible Server: 25–80 EUR
- Cache for Redis: 15–60 EUR (or self-host Redis on VM to save cost)
- Monitor/Backup: 5–15 EUR
- Total typical: ~65–150 EUR (can be ~45–80 EUR if Redis self-hosted and small VM)

Option C (AKS):
- AKS control plane: free, but node pools cost similar to VMs
- Managed DB/Cache costs as above
- Total typical: ~100–250+ EUR

Note: Prices vary by region and usage; these are indicative ranges.

## Pros of Migrating to Azure
- Managed services reduce manual setup and maintenance (Postgres, Redis, messaging)
- Built-in monitoring, logs, backups, security baselines
- Easier scaling and multi-zone resiliency options
- Enterprise-grade networking, TLS, identity, RBAC
- Potential for developer velocity with CI/CD integrations (GitHub Actions/Azure DevOps)

## Cons of Migrating to Azure
- Higher monthly cost vs single Hetzner box (likely 1.5–4x)
- Learning curve across multiple Azure services
- Yaml/config sprawl; more moving parts to operate
- Vendor lock-in considerations (Service Bus vs RabbitMQ semantics)
- Time to migrate, test, and tune (weeks for a solo developer)

## Recommended Path for a Solo Developer
1. Start with Option B (VM-first) to control costs and complexity.
   - Provision a small VM for containers; keep current Docker Compose flow.
   - Move Postgres to Azure Database for PostgreSQL (managed backups and HA).
   - Decide on Redis: managed Cache if SLA-critical; otherwise self-host on VM.
   - Keep RabbitMQ on VM initially, or plan switch to Service Bus later.
   - Use Azure Monitor + Log Analytics minimally for basics.

2. Incremental Modernization (only if needed):
   - Move selected services to Container Apps (stateless, HTTP workloads).
   - Frontend → Static Web Apps + CDN.
   - Replace RabbitMQ with Service Bus only if feature fit is acceptable.

3. CI/CD:
   - Use GitHub Actions to build and deploy containers/compose to VM.
   - For Container Apps, use `az containerapp up` or actions.

4. Cost Controls:
   - Use small SKUs; turn on auto-shutdown for dev/test.
   - Monitor Log Analytics ingestion; set retention appropriately.
   - Prefer a single region; avoid premium features until necessary.

## Migration Effort Estimate
- Option B (VM + managed Postgres): ~2–5 days total
  - VM setup (networking, SSH, Docker): 0.5–1 day
  - Postgres migrate + cutover: 1–2 days (test, backups)
  - Monitoring + backups + basic hardening: 0.5–1.5 days

- Option A (Container Apps + managed everything): ~1–2 weeks
  - Service decomposition, networking, secrets, CI/CD
  - Replacing RabbitMQ with Service Bus (if chosen): +2–4 days

## Decision Summary
- If the primary pain is manual ops on Hetzner and you're okay with a higher monthly bill, Azure can reduce operational overhead and increase reliability.
- For a solo developer, the best balance of cost/time is Option B: VM-first with managed Postgres.
- If your traffic and SLA needs grow, progressively move to Container Apps.

## Final Advice
- Stay on Hetzner if monthly budget is tight and manual ops are manageable; 40 EUR/month is very cost-effective.
- Migrate to Azure if you want managed DB/backups, standardized monitoring, and easier scaling, accepting a likely increase to ~65–150 EUR/month (Option B) and ~60–200+ EUR/month (Option A).
- Begin with VM + managed Postgres. Keep Redis/RabbitMQ on VM initially; migrate incrementally as needs dictate.
- Document a rollback plan and run a rehearsal cutover before switching DNS.

## Minimal Azure Checklist (Option B)
- Create Resource Group, VNet
- Provision VM (Linux), enable SSH, install Docker
- Provision Azure Database for PostgreSQL; migrate data (dump/restore)
- Configure security (NSGs, private endpoints if possible)
- Set up Azure Monitor + basic alerts
- Update `.env`/secrets and compose files; redeploy
- Test end-to-end; plan DNS cutover
