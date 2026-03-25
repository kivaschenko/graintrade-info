# Azure Deployment Guide

Complete step-by-step guide for deploying GrainTrade to Azure infrastructure.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Phase 1: Infrastructure Setup (Week 1)](#phase-1-infrastructure-setup)
3. [Phase 2: Service Deployment (Week 2)](#phase-2-service-deployment)
4. [Phase 3: Frontend Deployment (Week 3)](#phase-3-frontend-deployment)
5. [Phase 4: CI/CD Setup (Week 4)](#phase-4-cicd-setup)
6. [Phase 5: Testing & Cutover (Week 5)](#phase-5-testing--cutover)
7. [Troubleshooting](#troubleshooting)

---

## 📋 Prerequisites

### Required Tools

```bash
# 1. Azure CLI (https://docs.microsoft.com/cli/azure/install-azure-cli)
az --version

# 2. Terraform (https://www.terraform.io/downloads)
terraform --version

# 3. Docker & Docker Compose
docker --version
docker-compose --version

# 4. Git
git --version

# 5. Python 3.12+ (for testing)
python3 --version

# 6. Node.js 18+ (for frontend)
node --version
npm --version

# 7. jq (for JSON processing)
jq --version

# 8. PostgreSQL Client (psql)
psql --version
```

### Azure Subscription

- Free tier account: https://azure.microsoft.com/free/
- Startup credits: $200 (new accounts)
- Expected monthly cost: ~$100 (see cost section)

### GitHub Setup

- Repository must be public or GitHub Actions enabled
- Secrets must be configured in Settings > Secrets and variables > Actions

---

## Phase 1: Infrastructure Setup

### Step 1.1: Azure Account Setup

```bash
# Login to Azure
az login

# If you have multiple subscriptions
az account list --output table
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Verify
az account show --output jsonc
```

### Step 1.2: Create Resource Group (Optional - Terraform does this)

```bash
# Already handled by Terraform, but you can create manually
az group create --name graintrade-rg --location westeurope
```

### Step 1.3: Configure Terraform

```bash
cd terraform

# Copy example configuration
cp terraform.tfvars.example terraform.tfvars

# Get your public IP (needed for database access)
YOUR_IP=$(curl -s https://checkip.amazonaws.com)
echo "Your IP: $YOUR_IP"

# Edit terraform.tfvars with your values
nano terraform.tfvars
```

**Critical variables:**
```hcl
location                    = "westeurope"
resource_group_name         = "graintrade-rg"
storage_account_name        = "graintradesa$(date +%s)"  # Must be unique
container_registry_name     = "graintradeacr$(date +%s)" # Must be unique
postgres_admin_user         = "dbadmin"  # NOT "admin"
allowed_ip                  = "YOUR_IP_ADDRESS"
```

### Step 1.4: Initialize and Plan Terraform

```bash
# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Plan deployment (review output!)
terraform plan -out=tfplan

# Expected output sample:
# Plan: 23 to add, 0 to change, 0 to destroy.
```

### Step 1.5: Apply Terraform Configuration

```bash
# Deploy infrastructure (takes 15-30 minutes)
terraform apply tfplan

# Save outputs for next steps
terraform output > ../AZURE_OUTPUTS.json

# Export important values
export ACR_LOGIN_SERVER=$(terraform output -raw container_registry_login_server)
export POSTGRES_FQDN=$(terraform output -raw postgres_server_fqdn)
export REDIS_HOST=$(terraform output -raw redis_hostname)
export APP_INSIGHTS=$(terraform output -raw app_insights_instrumentation_key)

echo "Registry: $ACR_LOGIN_SERVER"
echo "PostgreSQL: $POSTGRES_FQDN"
echo "Redis: $REDIS_HOST"
```

### Step 1.6: Verify Infrastructure

```bash
# List all resources
az resource list --resource-group graintrade-rg --output table

# Check PostgreSQL status
az postgres flexible-server show --resource-group graintrade-rg --name graintrade-postgres

# Check Redis status
az redis show --resource-group graintrade-rg --name graintrade-redis

# Check App Service Plan
az appservice plan show --resource-group graintrade-rg --name appplan-graintrade
```

---

## Phase 2: Service Deployment

### Step 2.1: Build Docker Images

```bash
# Navigate to project root
cd ..

# Get ACR login credentials
az acr login --name graintradeacr

# Build backend image
docker build -t $ACR_LOGIN_SERVER/backend:latest ./backend
docker build -t $ACR_LOGIN_SERVER/backend:$GITHUB_SHA ./backend  # With commit hash

# Build chat-room image
docker build -t $ACR_LOGIN_SERVER/chat-room:latest ./chat-room

# Build notifications image
docker build -t $ACR_LOGIN_SERVER/notifications:latest ./notifications

# Build data-pipeline image
docker build -t $ACR_LOGIN_SERVER/data-pipeline:latest ./data-pipeline

# Verify images
docker images | grep graintradeacr
```

### Step 2.2: Push Images to Container Registry

```bash
# Push all images
docker push $ACR_LOGIN_SERVER/backend:latest
docker push $ACR_LOGIN_SERVER/chat-room:latest
docker push $ACR_LOGIN_SERVER/notifications:latest
docker push $ACR_LOGIN_SERVER/data-pipeline:latest

# Verify in registry
az acr repository list --name graintradeacr --output table
az acr repository show-tags --name graintradeacr --repository backend
```

### Step 2.3: Migrate Database

```bash
# Step 1: Backup current database (from Hetzner)
ssh user@65.108.68.57 'pg_dump -h localhost -U postgres -d graintrade' > backup-production.sql

# Step 2: Create PostgreSQL user and permissions
POSTGRES_PASSWORD=$(az keyvault secret show --vault-name graintrade-kv \
  --name postgres-admin-password --query value -o tsv)

# Step 3: Restore database to Azure
psql -h graintrade-postgres.postgres.database.azure.com \
  -U adminuser@graintrade-postgres \
  -d postgres \
  -f backup-production.sql

# Verify data migration
psql -h graintrade-postgres.postgres.database.azure.com \
  -U adminuser@graintrade-postgres \
  -d graintrade \
  -c "SELECT COUNT(*) FROM users;"  # Adjust table name as needed
```

### Step 2.4: Configure Backend App Service

```bash
# Get secrets from Key Vault
DB_URL=$(az keyvault secret show --vault-name graintrade-kv --name database-url --query value -o tsv)
REDIS_URL=$(az keyvault secret show --vault-name graintrade-kv --name redis-url --query value -o tsv)

# Set environment variables for backend
az webapp config appsettings set \
  --resource-group graintrade-rg \
  --name graintrade-backend \
  --settings \
    DATABASE_URL="$DB_URL" \
    REDIS_URL="$REDIS_URL" \
    RABBITMQ_URL="amqp://guest:guest@rabbitmq-host:5672/" \
    JWT_SECRET_KEY="$(openssl rand -base64 32)" \
    ENVIRONMENT="production" \
    LOG_LEVEL="INFO"

# Verify settings
az webapp config appsettings list \
  --resource-group graintrade-rg \
  --name graintrade-backend \
  --output table
```

### Step 2.5: Deploy Backend Service

```bash
# Option A: Deploy via Docker image
az webapp deployment container config \
  --resource-group graintrade-rg \
  --name graintrade-backend \
  --enable-continuous-deployment

# Set image in App Service
az webapp config container set \
  --resource-group graintrade-rg \
  --name graintrade-backend \
  --docker-custom-image-name "$ACR_LOGIN_SERVER/backend:latest" \
  --docker-registry-server-url "https://$ACR_LOGIN_SERVER" \
  --docker-registry-server-user "$(az acr credential show --name graintradeacr --query 'username' -o tsv)" \
  --docker-registry-server-password "$(az acr credential show --name graintradeacr --query 'passwords[0].value' -o tsv)"

# Wait for deployment
sleep 30

# Check logs
az webapp log tail --resource-group graintrade-rg --name graintrade-backend --lines 50

# Verify service is running
curl -I https://graintrade-backend.azurewebsites.net/health
```

### Step 2.6: Deploy Chat Room Service

```bash
# Configure chat room environment variables
az webapp config appsettings set \
  --resource-group graintrade-rg \
  --name graintrade-chat \
  --settings \
    DATABASE_URL="$DB_URL" \
    REDIS_URL="$REDIS_URL" \
    ENVIRONMENT="production" \
    LOG_LEVEL="INFO"

# Deploy image
az webapp config container set \
  --resource-group graintrade-rg \
  --name graintrade-chat \
  --docker-custom-image-name "$ACR_LOGIN_SERVER/chat-room:latest" \
  --docker-registry-server-url "https://$ACR_LOGIN_SERVER"

# Verify
curl -I https://graintrade-chat.azurewebsites.net/health
```

### Step 2.7: Deploy Notifications Container

```bash
# Update container with latest image
az container create \
  --resource-group graintrade-rg \
  --name notifications-container \
  --image "$ACR_LOGIN_SERVER/notifications:latest" \
  --cpu 0.5 --memory 1 \
  --restart-policy Always \
  --registry-login-server "$ACR_LOGIN_SERVER" \
  --registry-username "$(az acr credential show --name graintradeacr --query 'username' -o tsv)" \
  --registry-password "$(az acr credential show --name graintradeacr --query 'passwords[0].value' -o tsv)" \
  --environment-variables \
    DATABASE_URL="$DB_URL" \
    REDIS_URL="$REDIS_URL" \
    ENVIRONMENT="production"

# Check status
az container show --resource-group graintrade-rg --name notifications-container --query "instanceView.state"
```

### Step 2.8: Deploy RabbitMQ Container

```bash
# RabbitMQ is already deployed by Terraform, but you can verify it
az container show --resource-group graintrade-rg --name rabbitmq-container --query "instanceView.state"

# Get RabbitMQ IP address
RABBITMQ_IP=$(az container show --resource-group graintrade-rg --name rabbitmq-container --query ipAddress.ip -o tsv)
echo "RabbitMQ Address: $RABBITMQ_IP"

# Get RabbitMQ password from Key Vault
RABBITMQ_PASSWORD=$(az keyvault secret show --vault-name graintrade-kv \
  --name rabbitmq-password --query value -o tsv)

# Test RabbitMQ connectivity (from your machine or backend)
# Connection string: amqp://guest:$RABBITMQ_PASSWORD@$RABBITMQ_IP:5672/
# Management UI: http://$RABBITMQ_IP:15672 (username: guest, password from Key Vault)
```

### Step 2.9: Deploy Data Pipeline Container

```bash
# Deploy data pipeline
az container create \
  --resource-group graintrade-rg \
  --name data-pipeline-container \
  --image "$ACR_LOGIN_SERVER/data-pipeline:latest" \
  --cpu 2 --memory 4 \
  --restart-policy Never \
  --registry-login-server "$ACR_LOGIN_SERVER" \
  --environment-variables \
    DATABASE_URL="$DB_URL" \
    RUN_FORECAST="true" \
    ENVIRONMENT="production"

# For scheduled runs, use Azure Container Instances with Logic Apps or Timer Trigger
# Example: Run daily at 2 AM UTC
# This requires additional setup with Azure Logic Apps or Azure Functions
```

### Step 2.9: Deploy Data Pipeline Container

```bash
# Deploy data pipeline
az container create \
  --resource-group graintrade-rg \
  --name data-pipeline-container \
  --image "$ACR_LOGIN_SERVER/data-pipeline:latest" \
  --cpu 2 --memory 4 \
  --restart-policy Never \
  --registry-login-server "$ACR_LOGIN_SERVER" \
  --environment-variables \
    DATABASE_URL="$DB_URL" \
    RUN_FORECAST="true" \
    ENVIRONMENT="production"

# For scheduled runs, use Azure Container Instances with Logic Apps or Timer Trigger
# Example: Run daily at 2 AM UTC
# This requires additional setup with Azure Logic Apps or Azure Functions
```

### Step 2.10: Test Service Connectivity

```bash
# Test backend
curl -X GET https://graintrade-backend.azurewebsites.net/health
curl -X GET https://graintrade-backend.azurewebsites.net/docs

# Test chat service
curl -X GET https://graintrade-chat.azurewebsites.net/health

# Test RabbitMQ connectivity
RABBITMQ_IP=$(az container show --resource-group graintrade-rg --name rabbitmq-container --query ipAddress.ip -o tsv)
RABBITMQ_PASS=$(az keyvault secret show --vault-name graintrade-kv --name rabbitmq-password --query value -o tsv)

# Access RabbitMQ management UI: http://$RABBITMQ_IP:15672

# Test database connectivity from backend logs
az webapp log tail --resource-group graintrade-rg --name graintrade-backend --lines 20 | grep -i "database\|connected"

# Test Redis connectivity
redis-cli -h graintrade-redis.redis.cache.windows.net -p 6380 -a "KEY" ping
```

---

## Phase 3: Frontend Deployment

### Step 3.1: Create Static Web Apps Instance (Optional)

```bash
# Create Static Web Apps resource
az staticwebapp create \
  --name graintrade-frontend \
  --resource-group graintrade-rg \
  --location westeurope \
  --sku Free

# Get deployment token
DEPLOYMENT_TOKEN=$(az staticwebapp secrets list \
  --resource-group graintrade-rg \
  --name graintrade-frontend \
  --query "properties.apiKey" -o tsv)

echo "Deployment Token: $DEPLOYMENT_TOKEN"
```

### Step 3.2: Build Frontend

```bash
# Install dependencies
cd frontend
npm install

# Build production bundle
npm run build

# Verify dist folder
ls -la dist/

# Check bundle size
du -sh dist/
```

### Step 3.3: Deploy Frontend

```bash
# Option A: Manual deployment to Static Web Apps
az staticwebapp upload-files \
  --resource-group graintrade-rg \
  --name graintrade-frontend \
  --source-path ./dist

# Option B: Deploy to blob storage (if not using Static Web Apps)
az storage blob upload-batch \
  --destination '$web' \
  --source ./dist \
  --account-name graintradesa \
  --account-key "$(az storage account keys list --account-name graintradesa --query [0].value -o tsv)"

# Enable static website hosting
az storage account update --name graintradesa --account-key \
  "$(az storage account keys list --account-name graintradesa --query [0].value -o tsv)" \
  --set kind=StorageV2
```

### Step 3.4: Configure Frontend Routing

If using Static Web Apps, create `staticwebapp.config.json`:

```json
{
  "routes": [
    {
      "route": "/api/*",
      "allowedRoles": ["authenticated", "anonymous"]
    },
    {
      "route": "/*",
      "serve": "/index.html",
      "statusCode": 200
    }
  ],
  "navigationFallback": {
    "rewrite": "/index.html",
    "exclude": ["/images/*", "/css/*"]
  }
}
```

---

## Phase 4: CI/CD Setup

### Step 4.1: Configure GitHub Secrets

```bash
# Navigate to GitHub repository > Settings > Secrets and variables > Actions

# Required secrets:
# 1. AZURE_CREDENTIALS (for Azure authentication)
az ad sp create-for-rbac --name "github-actions" --role Contributor \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/graintrade-rg

# Output should look like:
# {
#   "clientId": "...",
#   "clientSecret": "...",
#   "subscriptionId": "...",
#   "tenantId": "..."
# }

# Copy the entire JSON output and add as AZURE_CREDENTIALS secret

# 2. Container Registry Credentials
az acr credential show --resource-group graintrade-rg --name graintradeacr

# Add these as separate secrets:
# - AZURE_REGISTRY_LOGIN_SERVER
# - AZURE_REGISTRY_USERNAME
# - AZURE_REGISTRY_PASSWORD

# 3. Static Web Apps Token (if using)
# - AZURE_STATIC_WEB_APPS_TOKEN (from Step 3.1)
```

### Step 4.2: Create GitHub Actions Workflow

The workflow file is already created at `.github/workflows/deploy.yml`

**To use it:**

```bash
# Verify the file exists
ls -la .github/workflows/deploy.yml

# Commit and push to GitHub
git add .github/workflows/deploy.yml
git commit -m "feat: Add Azure CI/CD deployment workflow"
git push origin develop

# Monitor in GitHub: Actions tab
```

### Step 4.3: Test CI/CD Pipeline

```bash
# Make a small change to trigger pipeline
echo "# Test deployment" >> backend/README.md

# Commit and push
git add backend/README.md
git commit -m "test: trigger CI/CD pipeline"
git push origin develop

# Watch the GitHub Actions execution:
# https://github.com/YOUR_USERNAME/graintrade-info/actions
```

---

## Phase 5: Testing & Cutover

### Step 5.1: Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test backend load handling
ab -n 1000 -c 10 https://graintrade-backend.azurewebsites.net/health

# Monitor during test
az monitor metrics list \
  --resource-group graintrade-rg \
  --resource-type microsoft.web/sites \
  --resource-name graintrade-backend \
  --metric "CpuPercentage" "MemoryPercentage" "RequestCount" \
  --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT1M
```

### Step 5.2: User Acceptance Testing

```bash
# Test critical user flows:
# 1. User registration and login
# 2. Create/view agricultural offers
# 3. Real-time chat functionality
# 4. Payment processing (if applicable)
# 5. Search and filtering

# Create test users in Azure PostgreSQL
psql -h graintrade-postgres.postgres.database.azure.com \
  -U adminuser@graintrade-postgres \
  -d graintrade
  
# Inside psql:
# INSERT INTO users (email, password, created_at) VALUES ('test@example.com', 'hashed_pwd', NOW());
```

### Step 5.3: Failover Testing

```bash
# Test Azure failover capabilities
# 1. Stop backend service - check if traffic reroutes
az webapp stop --resource-group graintrade-rg --name graintrade-backend

# Verify users see error page
curl -I https://graintrade-backend.azurewebsites.net/health

# Restart service
az webapp start --resource-group graintrade-rg --name graintrade-backend

# Verify recovery
curl -I https://graintrade-backend.azurewebsites.net/health
```

### Step 5.4: DNS Configuration

```bash
# Before final cutover, update DNS records pointing to Azure

# Get Azure endpoints:
echo "Frontend: $(az staticwebapp show --resource-group graintrade-rg --name graintrade-frontend --query 'properties.defaultDomain' -o tsv)"
echo "Backend: graintrade-backend.azurewebsites.net"
echo "Chat: graintrade-chat.azurewebsites.net"

# Update DNS records at your registrar:
# api.graintrade.info  → graintrade-backend.azurewebsites.net (CNAME)
# chat.graintrade.info → graintrade-chat.azurewebsites.net (CNAME)
# graintrade.info      → Azure Static Web Apps endpoint (CNAME)

# Verify DNS propagation
nslookup api.graintrade.info
nslookup graintrade.info
```

### Step 5.5: SSL/TLS Configuration

```bash
# Add custom domain with SSL certificate
az webapp config hostname add \
  --resource-group graintrade-rg \
  --webapp-name graintrade-backend \
  --hostname api.graintrade.info

# Azure App Service provides free managed certificate for *.azurewebsites.net
# For custom domains, either:
# Option A: Use Azure managed certificate (free)
az webapp config ssl bind \
  --resource-group graintrade-rg \
  --name graintrade-backend \
  --certificate-thumbprint THUMBPRINT

# Option B: Use Let's Encrypt (via certbot)
# certbot certonly --dns-azure -d api.graintrade.info -d graintrade.info
```

### Step 5.6: Monitor Cutover

```bash
# Set up real-time monitoring during cutover
watch -n 1 'az monitor metrics list --resource-group graintrade-rg --resource-type microsoft.web/sites --resource-name graintrade-backend --metric RequestCount --start-time $(date -u -d "5 minutes ago" +%Y-%m-%dT%H:%M:%SZ) --interval PT1M'

# Monitor Application Insights
echo "Application Insights: https://portal.azure.com/#resource/subscriptions/YOUR_SUB/resourceGroups/graintrade-rg/providers/microsoft.insights/components/appinsights-graintrade"

# Check error rates
az monitor metrics list \
  --resource-group graintrade-rg \
  --resource-name appinsights-graintrade \
  --resource-type microsoft.insights/components \
  --metric "server/exceptions" \
  --interval PT1M
```

### Step 5.7: Decommission Hetzner Server

```bash
# Only after confirming stable operation on Azure (24-48 hours minimum)

# Final backup from Hetzner
ssh user@65.108.68.57 'pg_dump -h localhost -U postgres -d graintrade' > final-backup-production.sql

# Shutdown services on Hetzner
ssh user@65.108.68.57 'cd /home/kivaschenko/graintrade-info && docker-compose down'

# Cancel server with hosting provider (or keep as standby for 1 month)
```

---

## Troubleshooting

### Common Issues

#### PostgreSQL Connection Fails

```bash
# Check firewall rules
az postgres flexible-server firewall-rule list \
  --resource-group graintrade-rg \
  --name graintrade-postgres

# Add rule for your IP if needed
az postgres flexible-server firewall-rule create \
  --resource-group graintrade-rg \
  --name graintrade-postgres \
  --rule-name AllowMyIP \
  --start-ip-address YOUR_IP \
  --end-ip-address YOUR_IP

# Test connection
psql -h graintrade-postgres.postgres.database.azure.com \
  -U adminuser@graintrade-postgres \
  -d graintrade -c "SELECT 1;"
```

#### App Service Not Starting

```bash
# Check app service logs
az webapp log download --resource-group graintrade-rg --name graintrade-backend

# Check container logs
az webapp log tail --resource-group graintrade-rg --name graintrade-backend --lines 100

# Restart service
az webapp restart --resource-group graintrade-rg --name graintrade-backend

# Check health
az webapp show --resource-group graintrade-rg --name graintrade-backend --query "state"
```

#### Docker Image Pull Fails

```bash
# Verify image exists in registry
az acr repository list --name graintradeacr

# Check image tags
az acr repository show-tags --name graintradeacr --repository backend

# Verify credentials are correct
az acr credential show --name graintradeacr

# Repush image if needed
docker push $ACR_LOGIN_SERVER/backend:latest
```

#### High Costs

```bash
# Check current resource utilization
az monitor metrics list \
  --resource-group graintrade-rg \
  --resource-type microsoft.web/sites \
  --resource-name graintrade-backend \
  --metric "CpuPercentage" "MemoryPercentage"

# Scale down if not needed
az appservice plan update --resource-group graintrade-rg \
  --name appplan-graintrade --sku B0

# Delete unused resources
terraform destroy -target azurerm_container_group.notifications
```

---

## Post-Deployment Checklist

- [ ] Infrastructure deployed successfully via Terraform
- [ ] Docker images built and pushed to ACR
- [ ] Database migrated from Hetzner to Azure PostgreSQL
- [ ] All environment variables configured in App Services
- [ ] Backend service healthy at `/health` endpoint
- [ ] Chat room service healthy at `/health` endpoint
- [ ] Frontend deployed and accessible
- [ ] GitHub Actions workflow configured and tested
- [ ] SSL certificates configured for custom domains
- [ ] DNS records pointing to Azure endpoints
- [ ] Monitoring and alerts configured
- [ ] Backup strategy implemented
- [ ] Disaster recovery tested
- [ ] Performance acceptable under load
- [ ] Cost monitoring set up
- [ ] Hetzner server decommissioned (if cutover complete)

---

## Cost Optimization Summary

### Before (Hetzner)
- €27/month = €324/year

### After (Azure with startup)
- ~$100/month = $1,200/year
- Free tier credits: $200 (first 2 months)
- **Net cost: ~$900/year after credits**

### Break-even point: 4 months

### Ways to reduce costs further:
1. Use Reserved Instances (35% savings after 6 months)
2. Set up auto-scaling rules to reduce capacity during off-hours
3. Archive old data-pipeline results to cold storage
4. Use spot instances for non-critical workloads

---

## Support

For issues:
1. Check Azure Portal for resource status
2. Review Application Insights for errors
3. Check logs: `az webapp log tail ...`
4. Consult Terraform state: `terraform show`
5. Review GitHub Actions logs for CI/CD issues

---

**Document Version**: 1.0  
**Last Updated**: January 20, 2026  
**Next Review**: February 20, 2026
