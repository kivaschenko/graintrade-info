# GrainTrade: Hetzner to Azure Migration Guide

**Date**: January 20, 2026  
**Current Deployment**: Hetzner dedicated server (65.108.68.57)  
**Target Deployment**: Azure Container Instances + App Service + Managed PostgreSQL  
**Cost Optimization**: Minimal startup costs with scalability  

---

## 📊 Executive Summary

This document outlines a comprehensive migration strategy from a Hetzner dedicated server to Azure cloud infrastructure. The migration prioritizes:

1. **Cost Efficiency** - Leveraging Azure's pay-as-you-go model with startup discounts
2. **Scalability** - Moving from fixed hardware to elastic cloud resources
3. **DevOps Automation** - GitHub Actions replacing Jenkins for CI/CD
4. **Operational Efficiency** - Managed services reducing infrastructure maintenance

### Cost Comparison

**Current Hetzner Setup:**
- Dedicated server (AMD EPYC 8-core, 32GB RAM, 400GB NVMe): €27/month
- Estimated annual cost: **€324**
- Scaling requires new hardware procurement

**Proposed Azure Setup (Startup Phase):**
- Azure App Service (B1 - 1 vCore, 1.75 GB): $11/month
- PostgreSQL Flexible Server (Burstable B1ms): $57/month
- Redis Cache (Basic C0): $12.50/month
- Container Registry (Basic): $5/month
- Storage (for data-pipeline): $5/month
- Network & miscellaneous: $10/month
- **Total estimated: ~$100/month or €92/month (with startup credits)**

**Initial 12-month cost**: ~$1,200 USD (including free tier consumption)  
**Break-even**: 4 months (after which Hetzner becomes more economical)

---

## 🏗️ Current Architecture Analysis

### Services Overview

| Service | Framework | Language | Port | Dependencies |
|---------|-----------|----------|------|--------------|
| **Backend** | FastAPI | Python 3.12 | 8000 | PostgreSQL, Redis, RabbitMQ |
| **Chat Room** | FastAPI | Python 3.12 | 8001 | PostgreSQL, Redis, RabbitMQ |
| **Notifications** | FastAPI | Python 3.12 | 8002 | PostgreSQL, Redis, RabbitMQ, SMTP |
| **Data Pipeline** | FastAPI | Python 3.12 | 8004 | PostgreSQL, RabbitMQ, S3/Blob Storage |
| **Landing Service** | Flask | Python | 8003 | Static files |
| **Frontend** | Vue.js 3 | JavaScript | 8080 | Backend APIs |
| **Infrastructure** | Postgres + RabbitMQ + Redis | - | 5432, 5672, 6379 | - |

### Current Deployment Method
- **Server**: Single Hetzner dedicated server
- **Orchestration**: Docker Compose
- **CI/CD**: Jenkins (on Gitea)
- **Reverse Proxy**: Apache2 with SSL
- **Monitoring**: Prometheus + Grafana

### Key Infrastructure Services

1. **PostgreSQL 16+**: Primary application database
2. **RabbitMQ**: Message broker for microservice communication
3. **Redis**: Distributed cache and session storage
4. **Apache2**: Reverse proxy with SSL termination

---

## 🎯 Azure Migration Strategy

### Phase 1: Quick Migration (Week 1)
Deploy to Azure Container Instances with managed services

### Phase 2: Production Optimization (Week 2-3)
Migrate to App Service with auto-scaling and improve CI/CD

### Phase 3: Performance Tuning (Week 4+)
Optimize database, caching, and implement Azure monitoring

---

## 📋 Azure Resource Mapping

### Option A: Container Instances (Quick Setup)

```
Frontend (Static Site) → Azure Static Web Apps
                          ↓
            ┌─────────────┴─────────────┐
            ↓                           ↓
Backend Containers                  Chat Room
(Container Instances)                (Container Instances)
    ↓                                   ↓
PostgreSQL Flexible Server (Managed)
    ↑ ↓
Redis Cache                         Notifications
(Azure Cache for Redis)            (Container Instances)
                                        ↓
                    Data Pipeline (Container Instances or Batch)
                            ↓
                    Azure Blob Storage
                    (for Delta Lake)
```

### Option B: App Service (Recommended for Startup)

```
Frontend                Backend App Service       Chat App Service
(Static Web Apps)      (B1: 1 vCore, 1.75GB)    (B2: 2 vCore)
    ↓                          ↓                      ↓
                    PostgreSQL Flexible Server
                    (Burstable B1ms)
                            ↑ ↓
                    Azure Cache for Redis
                    (Basic C0)
                            ↑ ↓
                    Notifications Service         Data Pipeline
                    (Container Instance)        (Container Instance)
                            ↓
                    Azure Blob Storage
```

### Option C: Hybrid (Enterprise Grade)

Combine App Service + Container Instances + AKS (Kubernetes) - **Not recommended for startup**

---

## 🚀 Recommended Architecture: Option B

### Why Option B?

1. **Cost-effective**: $11/month for unlimited scaling within tier
2. **Managed**: No infrastructure maintenance
3. **Auto-scaling**: Built-in support for traffic spikes
4. **CI/CD friendly**: GitHub Actions integration is native
5. **Monitoring**: Azure Monitor included

### Resource List

#### Compute
- **Backend App Service**: B1 tier (1 vCore, 1.75 GB RAM)
- **Chat Room App Service**: B1 tier (shared with backend or separate)
- **Notifications Container Instance**: 0.25 vCore, 0.5 GB (on-demand)
- **RabbitMQ Container Instance**: 1 vCore, 2 GB (always-on message broker)
- **Data Pipeline**: Scheduled Container Instance (daily/weekly)

#### Database & Cache
- **PostgreSQL Flexible Server**: Burstable B1ms (1 vCore, 2GB)
  - Suitable for 50-100 concurrent users
  - Automatic backups (35 days)
  - Read replicas available for scaling
- **Azure Cache for Redis**: Basic C0 (256 MB)
  - Session caching and real-time chat data
  - Auto-purge after 24 hours for free tier

#### Storage
- **Azure Blob Storage**: Standard tier
  - Data pipeline results (Delta Lake format)
  - Frontend static assets (optional)
- **Azure Container Registry**: Basic tier
  - Docker image storage and management

#### Networking
- **Virtual Network**: Standard VNet
  - Private endpoints for PostgreSQL and Redis
  - Service endpoints for secure communication
- **Application Gateway** (optional): For load balancing if scaling

#### Security
- **Key Vault**: Store secrets, connection strings, API keys
- **Managed Identity**: For secure service-to-service authentication
- **Network Security Groups**: Firewall rules

---

## 📦 Service-by-Service Migration Plan

### 1. Backend Service (FastAPI)

**Current**: Running on port 8000, Ubuntu VM

**Target**: Azure App Service (Python runtime)

**Migration Steps**:
```bash
# 1. Create App Service Plan
az appservice plan create --name graintrade-plan --resource-group graintrade-rg --sku B1 --is-linux

# 2. Create App Service
az webapp create --resource-group graintrade-rg --plan graintrade-plan --name graintrade-api --runtime "PYTHON|3.12"

# 3. Configure deployment
az webapp deployment source config-zip --resource-group graintrade-rg --name graintrade-api --src backend.zip

# 4. Set environment variables
az webapp config appsettings set --resource-group graintrade-rg --name graintrade-api --settings @backend-env.json
```

**Environment Variables** (stored in Key Vault):
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `RABBITMQ_URL`: RabbitMQ connection string
- `JWT_SECRET_KEY`: Encryption key
- `SMTP_PASSWORD`: Email service credentials

### 2. Chat Room Service (FastAPI)

**Migration**: Same as backend, separate App Service or co-located

**Decision Matrix**:
- Co-locate if: Chat traffic < 20% of total requests
- Separate if: Real-time chat requires isolation or runs long connections

**Recommendation**: Separate B1 App Service for chat (WebSocket connections)

### 3. Notifications Service (FastAPI)

**Migration**: Azure Container Instances (scheduled or always-on)

**Rationale**: 
- Lower traffic (background notifications)
- Can use Consumption-based pricing
- Runs 24/7 but doesn't need App Service overhead

**Implementation**:
```bash
az container create --resource-group graintrade-rg \
  --name graintrade-notifications \
  --image graintrade.azurecr.io/notifications:latest \
  --cpu 0.25 --memory 0.5 \
  --environment-variables DATABASE_URL=... REDIS_URL=... \
  --restart-policy Always
```

### 4. Data Pipeline Service

**Current**: Runs in Docker Compose, scheduled jobs

**Target**: Azure Container Instances (scheduled) + Azure Batch (optional)

**Migration**:
```bash
# Create container instance
az container create --resource-group graintrade-rg \
  --name graintrade-data-pipeline \
  --image graintrade.azurecr.io/data-pipeline:latest \
  --cpu 2 --memory 4 \
  --environment-variables RUN_FORECAST=true \
  --restart-policy Never

# Schedule with Azure Logic Apps (equivalent of cron)
```

### 5. Landing Service (Flask)

**Current**: Flask app on port 8003

**Target**: Azure Static Web Apps (if static) or App Service (if dynamic)

**Decision**: 
- If mostly static (marketing pages): Azure Static Web Apps (FREE tier)
- If dynamic content: Lightweight App Service B0/B1

**Recommendation**: Azure Static Web Apps (free hosting)

### 6. Frontend (Vue.js)

**Current**: Node.js build → static site served on port 8080

**Target**: Azure Static Web Apps

**Migration**:
```bash
# Build Vue application
npm run build

# Deploy to Azure Static Web Apps
az staticwebapp create --name graintrade-frontend \
  --resource-group graintrade-rg \
  --source https://github.com/your-repo/graintrade-info \
  --location "westeurope" \
  --build-folder "dist"
```

### 7. PostgreSQL Database

**Current**: Self-managed on Hetzner

**Target**: Azure Database for PostgreSQL Flexible Server

**Migration Steps**:

1. **Create Azure PostgreSQL**:
```bash
az postgres flexible-server create \
  --resource-group graintrade-rg \
  --name graintrade-postgres \
  --location westeurope \
  --admin-user adminuser \
  --admin-password "$(openssl rand -base64 32)" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --backup-retention 7 \
  --high-availability Disabled
```

2. **Migrate Data** (using pg_dump):
```bash
# On Hetzner server
pg_dump -h localhost -U postgres -d graintrade > backup.sql

# Upload to Azure
psql -h graintrade-postgres.postgres.database.azure.com \
  -U adminuser@graintrade-postgres \
  -d postgres < backup.sql
```

3. **Update Connection Strings**: All services will use new Azure PostgreSQL endpoint

### 8. RabbitMQ

**Current**: Self-managed on Hetzner

**Target**: Azure Container Instance (RabbitMQ 4.0 with Management UI)

**Migration Strategy**:

Terraform automatically deploys RabbitMQ on Azure Container Instance:
- No code changes required
- Compatible with existing AMQP clients
- Includes management UI for monitoring

**After Deployment**:
```bash
# Get RabbitMQ IP and credentials
RABBITMQ_IP=$(az container show --resource-group graintrade-rg \
  --name rabbitmq-container --query ipAddress.ip -o tsv)

RABBITMQ_PASSWORD=$(az keyvault secret show --vault-name graintrade-kv \
  --name rabbitmq-password --query value -o tsv)

# Connection string for all services
RABBITMQ_URL=amqp://guest:${RABBITMQ_PASSWORD}@${RABBITMQ_IP}:5672/

# Management UI
# Access: http://$RABBITMQ_IP:15672
# Username: guest
# Password: (from Key Vault)
```

**Configuration**:
- Username: `guest` (default)
- Password: Auto-generated and stored in Key Vault
- AMQP Port: 5672
- Management UI Port: 15672
- Auto-restart: Enabled
- Resources: 1 vCore, 2 GB memory

**Optional**: If you prefer Azure Service Bus instead:
- Fully managed queue/topic service
- Better for very large scale (1000+ msgs/sec)
- Requires code changes (switch from AMQP to Service Bus SDK)

### 9. Redis Cache

**Current**: Self-managed on Hetzner

**Target**: Azure Cache for Redis

**Migration**:
```bash
az redis create --resource-group graintrade-rg \
  --name graintrade-redis \
  --location westeurope \
  --sku Basic --vm-size c0

# Update connection strings in all services
REDIS_URL=graintrade-redis.redis.cache.windows.net:6380
```

---

## 🔐 Security Best Practices

### Network Security

1. **Private Endpoints**:
   - PostgreSQL: Private endpoint in VNet
   - Redis: Private endpoint in VNet
   - Storage account: Service endpoint

2. **Network Security Groups** (Firewall):
   ```json
   {
     "inbound_rules": [
       {"source": "*", "port": 443, "protocol": "tcp", "description": "HTTPS"},
       {"source": "VNet", "port": 5432, "protocol": "tcp", "description": "PostgreSQL"},
       {"source": "VNet", "port": 6379, "protocol": "tcp", "description": "Redis"}
     ]
   }
   ```

3. **SSL/TLS**:
   - App Service: Free managed certificate (*.azurewebsites.net)
   - Custom domain: Use Azure Key Vault for SSL certificates

### Secrets Management

All sensitive data stored in Azure Key Vault:
```bash
az keyvault secret set --vault-name graintrade-kv --name DATABASE-PASSWORD --value "..."
az keyvault secret set --vault-name graintrade-kv --name REDIS-KEY --value "..."
az keyvault secret set --vault-name graintrade-kv --name JWT-SECRET --value "..."
```

Access via Managed Identity from App Service (no hardcoded secrets)

### Monitoring & Alerts

- **Azure Monitor**: CPU, memory, request latency
- **Application Insights**: Exception tracking, performance monitoring
- **Log Analytics**: Centralized logging for all services

---

## 🚀 Deployment Timeline

### Week 1: Infrastructure Setup
- [ ] Create Azure resource group and storage account
- [ ] Set up PostgreSQL Flexible Server with migration
- [ ] Create Redis cache instance
- [ ] Create Container Registry
- [ ] Set up Key Vault with secrets

### Week 2: Service Deployment
- [ ] Deploy backend App Service
- [ ] Deploy chat room App Service
- [ ] Deploy notifications Container Instance
- [ ] Deploy data pipeline Container Instance
- [ ] Deploy landing service (static or lightweight)

### Week 3: Frontend & CI/CD
- [ ] Build and deploy Vue.js frontend to Static Web Apps
- [ ] Set up GitHub Actions workflows
- [ ] Configure auto-scaling policies
- [ ] Set up monitoring and alerting

### Week 4: Optimization & Cutover
- [ ] Performance testing and optimization
- [ ] Update DNS to point to Azure
- [ ] Monitor for issues and adjust resources
- [ ] Decommission Hetzner server

---

## 💰 Cost Optimization Tips

### 1. **Use Startup Credits**
- Azure provides $200 free credits for new accounts
- Use for first 2 months of testing

### 2. **Reserved Instances** (3-6 months out)
- If traffic is stable, reserve App Service instances
- Saves ~35% compared to pay-as-you-go

### 3. **Spot Instances for Non-Critical Workloads**
- Data pipeline can run on spot VMs (savings: 70-90%)
- Example: `az container create --priority Spot`

### 4. **Consolidate Services**
- Run multiple lightweight services on single B1 App Service
- Use App Service Slots for staging/production

### 5. **Database Optimization**
- Start with B1ms tier; scale down to B0 if underutilized
- Enable storage autogrow to avoid surprise costs

### 6. **Storage Efficiency**
- Use Azure Blob Storage lifecycle policies
- Archive old data pipeline results after 30 days

---

## 🔄 Rollback Strategy

### Pre-Migration Checklist
1. **Full database backup**: Download pg_dump of production DB
2. **Code freeze**: Ensure stable version deployed
3. **DNS TTL**: Set to 5 minutes before cutover
4. **Monitoring**: Set up Azure alerts before going live

### During Migration
- Run Azure and Hetzner in parallel for 24-48 hours
- Gradually shift traffic (10% → 50% → 100%)
- Monitor error rates and latency continuously

### Rollback Procedure (if needed)
```bash
# DNS failover to Hetzner (5 min downtime)
az network dns record-set a update --resource-group ... \
  --zone-name graintrade.info \
  --name www \
  --ipv4-address 65.108.68.57

# Services on Hetzner already running, automatic failover
```

---

## 📊 Monitoring & Observability

### Azure Monitor Setup

1. **Metrics to track**:
   - App Service CPU, memory, request count
   - PostgreSQL connections, query latency
   - Redis cache hit ratio
   - Container instance restarts

2. **Alerts**:
   - CPU > 80%: Scale up or optimize
   - Database connections > 80 of max
   - Error rate > 1%
   - Response time > 5 seconds

3. **Dashboards**:
   - Real-time service health
   - Cost tracking (Azure Cost Management)
   - Request latency percentiles (p50, p95, p99)

### Application Insights

Instrument FastAPI/Vue.js with Application Insights SDK:

```python
# backend/app/main.py
from azure.monitor.opentelemetry import configure_azure_monitor

configure_azure_monitor(connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"))
```

---

## 📚 Implementation Files Included

This migration includes the following ready-to-use files:

1. **terraform/** - Complete Terraform configuration
   - `main.tf` - Resource definitions
   - `variables.tf` - Input variables
   - `outputs.tf` - Output values
   - `terraform.tfvars.example` - Example values

2. **.github/workflows/deploy.yml** - GitHub Actions CI/CD pipeline
   - Automated testing
   - Docker image build and push
   - Deployment to Azure

3. **deployment-guide.md** - Step-by-step deployment instructions

4. **docker-compose.azure.yml** - Docker Compose for local testing

---

## ❓ FAQ

### Q: Will my current codebase work on Azure without changes?
**A**: Yes! Azure Container Instances and App Service run Docker containers. Your `Dockerfile` and `docker-compose.yaml` are compatible.

### Q: How long is the migration?
**A**: 2-4 weeks depending on testing requirements. Quick setup (24-48 hours), then optimization and testing.

### Q: What if I need to rollback?
**A**: Keep Hetzner running in parallel for 48 hours. DNS can be switched back in minutes.

### Q: Can I use my current domain (graintrade.info)?
**A**: Yes! Update DNS records to point to Azure:
- Frontend: Azure Static Web Apps endpoint
- API: App Service endpoint
- Both can be behind Azure Application Gateway for unified endpoint

### Q: How do I scale if I get more users?
**A**: 
- **Backend**: Upgrade B1 → B2 → Standard S1/S2 (or use auto-scaling)
- **PostgreSQL**: Scale from B1ms → D2s → upgrade tier
- **Redis**: B tier → C tier
- **Horizontal scaling**: Deploy multiple App Service instances with Load Balancer

### Q: Is this cheaper than Hetzner long-term?
**A**: 
- **0-6 months**: Azure (with startup credits)
- **6-12 months**: Roughly equivalent
- **12+ months**: Hetzner becomes cheaper if traffic stable
- **With growth**: Azure becomes cheaper (no hardware procurement)

---

## 🔗 Next Steps

1. **Review** this document with your team
2. **Verify** resource list and costs using Azure Pricing Calculator
3. **Prepare** Terraform variables for your environment
4. **Test** infrastructure deployment in non-production first
5. **Configure** GitHub Actions for automated deployments
6. **Execute** phased migration according to timeline

---

## 📞 Support & Resources

- **Azure Documentation**: https://docs.microsoft.com/azure
- **Terraform Azure Provider**: https://registry.terraform.io/providers/hashicorp/azurerm/latest
- **GitHub Actions**: https://docs.github.com/actions
- **Cost Calculator**: https://azure.microsoft.com/en-us/pricing/calculator/

---

**Document Version**: 1.0  
**Last Updated**: January 20, 2026  
**Next Review**: February 20, 2026
