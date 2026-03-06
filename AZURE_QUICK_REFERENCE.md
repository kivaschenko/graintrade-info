# Azure Deployment Quick Reference

**TL;DR** - Copy/paste commands for common operations.

## 🚀 Initial Setup (First Time)

```bash
# 1. Install tools
az --version  # Should be 2.50+
terraform --version  # Should be 1.0+
docker --version  # Should be 20+

# 2. Authenticate
az login
az account set --subscription "YOUR_SUB_ID"

# 3. Setup Terraform
cd terraform
cp terraform.tfvars.example terraform.tfvars

# Get your IP
curl https://checkip.amazonaws.com

# Edit terraform.tfvars with:
# - location: "westeurope"
# - storage_account_name: "graintradesa" + random (must be unique)
# - container_registry_name: "graintradeacr" + random
# - allowed_ip: (your IP from above)
# - postgres_admin_user: "dbadmin"

nano terraform.tfvars

# 4. Deploy infrastructure
terraform init
terraform plan
terraform apply  # This takes 15-30 minutes

# 5. Get outputs
terraform output -json > ../AZURE_OUTPUTS.json
export ACR_REGISTRY=$(terraform output -raw container_registry_login_server)
export POSTGRES_FQDN=$(terraform output -raw postgres_server_fqdn)
export REDIS_HOST=$(terraform output -raw redis_hostname)
```

## 🐳 Build and Push Docker Images

```bash
# Login to registry
az acr login --name graintradeacr

# Build images
docker build -t ${ACR_REGISTRY}/backend:latest ./backend
docker build -t ${ACR_REGISTRY}/chat-room:latest ./chat-room
docker build -t ${ACR_REGISTRY}/notifications:latest ./notifications
docker build -t ${ACR_REGISTRY}/data-pipeline:latest ./data-pipeline

# Push images
docker push ${ACR_REGISTRY}/backend:latest
docker push ${ACR_REGISTRY}/chat-room:latest
docker push ${ACR_REGISTRY}/notifications:latest
docker push ${ACR_REGISTRY}/data-pipeline:latest

# Verify
az acr repository list --name graintradeacr
```

## 🐰 RabbitMQ Setup

```bash
# Get RabbitMQ IP and credentials
RABBITMQ_IP=$(az container show --resource-group graintrade-rg --name rabbitmq-container --query ipAddress.ip -o tsv)
RABBITMQ_PASS=$(az keyvault secret show --vault-name graintrade-kv --name rabbitmq-password --query value -o tsv)

# Connection string for services
RABBITMQ_URL="amqp://guest:${RABBITMQ_PASS}@${RABBITMQ_IP}:5672/"

# Access management UI
echo "RabbitMQ Management: http://${RABBITMQ_IP}:15672"
echo "Username: guest"
echo "Password: (see Key Vault secret)"

# Test RabbitMQ connectivity
# From a container or your machine:
# python3 -c "import pika; conn = pika.BlockingConnection(pika.URLParameters('$RABBITMQ_URL'))"
```

## 💾 Database Migration

```bash
# 1. Backup from Hetzner
ssh user@65.108.68.57 'pg_dump -h localhost -U postgres -d graintrade' > backup.sql

# 2. Get admin password from Key Vault
PG_PASS=$(az keyvault secret show --vault-name graintrade-kv \
  --name postgres-admin-password --query value -o tsv)

# 3. Restore to Azure
psql -h ${POSTGRES_FQDN} -U adminuser@graintrade-postgres -d postgres < backup.sql

# 4. Verify
psql -h ${POSTGRES_FQDN} -U adminuser@graintrade-postgres -d graintrade -c "SELECT COUNT(*) FROM users;"
```

## 🚢 Deploy Services

```bash
# Get connection strings from Key Vault
DB_URL=$(az keyvault secret show --vault-name graintrade-kv --name database-url --query value -o tsv)
REDIS_URL=$(az keyvault secret show --vault-name graintrade-kv --name redis-url --query value -o tsv)

# Deploy Backend
az webapp config container set \
  --resource-group graintrade-rg \
  --name graintrade-backend \
  --docker-custom-image-name "${ACR_REGISTRY}/backend:latest" \
  --docker-registry-server-url "https://${ACR_REGISTRY}" \
  --docker-registry-server-user "$(az acr credential show --name graintradeacr --query username -o tsv)" \
  --docker-registry-server-password "$(az acr credential show --name graintradeacr --query 'passwords[0].value' -o tsv)"

# Set environment variables for Backend
az webapp config appsettings set --resource-group graintrade-rg --name graintrade-backend \
  --settings \
    DATABASE_URL="$DB_URL" \
    REDIS_URL="$REDIS_URL" \
    ENVIRONMENT="production"

# Deploy Chat Room (same process)
az webapp config container set \
  --resource-group graintrade-rg \
  --name graintrade-chat \
  --docker-custom-image-name "${ACR_REGISTRY}/chat-room:latest" \
  --docker-registry-server-url "https://${ACR_REGISTRY}"

# Verify
curl -I https://graintrade-backend.azurewebsites.net/health
curl -I https://graintrade-chat.azurewebsites.net/health
```

## 🔍 Monitoring & Debugging

```bash
# View app logs (real-time)
az webapp log tail --resource-group graintrade-rg --name graintrade-backend --lines 50

# Download all logs
az webapp log download --resource-group graintrade-rg --name graintrade-backend

# Check app status
az webapp show --resource-group graintrade-rg --name graintrade-backend --query "state"

# View metrics
az monitor metrics list \
  --resource-group graintrade-rg \
  --resource-type microsoft.web/sites \
  --resource-name graintrade-backend \
  --metric RequestCount CpuPercentage MemoryPercentage \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT5M \
  --output table

# View Application Insights errors
az monitor app-insights metrics show \
  --resource-group graintrade-rg \
  --app appinsights-graintrade \
  --metric "requests/failed" \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)
```

## 🔄 Scale Services

```bash
# Scale up App Service Plan
az appservice plan update \
  --resource-group graintrade-rg \
  --name appplan-graintrade \
  --sku B2  # Options: B0, B1, B2, B3, S1, S2, S3

# Scale out (add instances)
az appservice plan update \
  --resource-group graintrade-rg \
  --name appplan-graintrade \
  --number-of-workers 2

# Scale PostgreSQL
az postgres flexible-server update \
  --resource-group graintrade-rg \
  --name graintrade-postgres \
  --sku-name Standard_D2s_v3  # Bigger tier

# Scale Redis
az redis update \
  --resource-group graintrade-rg \
  --name graintrade-redis \
  --sku Standard  # From Basic to Standard
```

## 🔄 Restart Services

```bash
# Restart Web App
az webapp restart --resource-group graintrade-rg --name graintrade-backend

# Restart all containers
az container restart --resource-group graintrade-rg --name notifications-container
az container restart --resource-group graintrade-rg --name rabbitmq-container
az container restart --resource-group graintrade-rg --name data-pipeline-container

# Redeploy with new image (auto-pull latest)
az webapp deployment container config \
  --resource-group graintrade-rg \
  --name graintrade-backend \
  --enable-continuous-deployment
```

## 🌐 DNS & SSL

```bash
# Add custom domain
az webapp config hostname add \
  --resource-group graintrade-rg \
  --webapp-name graintrade-backend \
  --hostname api.graintrade.info

# Bind certificate (auto-managed)
az webapp config ssl bind \
  --resource-group graintrade-rg \
  --name graintrade-backend \
  --certificate-thumbprint YOUR_THUMBPRINT

# List current bindings
az webapp config hostname list \
  --resource-group graintrade-rg \
  --webapp-name graintrade-backend
```

## 💲 Cost & Cleanup

```bash
# Estimate monthly costs
echo "App Service B1: $11"
echo "PostgreSQL B1ms: $57"
echo "Redis Basic C0: $12.50"
echo "Container Registry: $5"
echo "Storage: $5"
echo "---"
echo "Total: ~$90-100/month"

# View actual costs (requires Cost Management)
az costmanagement query \
  --timeframe MonthToDate \
  --type "Usage" \
  --dataset '{"granularity":"Daily","aggregation":{"totalCost":{"name":"PreTaxCost","function":"Sum"}}}' \
  --filter '{"dimensions":{"name":"ResourceGroup","operator":"In","values":["graintrade-rg"]}}'

# Destroy all resources (WARNING!)
cd terraform
terraform destroy

# Verify everything is deleted
az resource list --resource-group graintrade-rg
```

## 🔑 Secret Management

```bash
# Create a secret
az keyvault secret set \
  --vault-name graintrade-kv \
  --name my-secret \
  --value "secret-value"

# Get a secret
az keyvault secret show \
  --vault-name graintrade-kv \
  --name database-url \
  --query value -o tsv

# List all secrets
az keyvault secret list --vault-name graintrade-kv

# Delete a secret
az keyvault secret delete --vault-name graintrade-kv --name old-secret
```

## 🔐 Security

```bash
# Add IP to PostgreSQL whitelist
YOUR_IP=$(curl -s https://checkip.amazonaws.com)

az postgres flexible-server firewall-rule create \
  --resource-group graintrade-rg \
  --name graintrade-postgres \
  --rule-name MyIP \
  --start-ip-address $YOUR_IP \
  --end-ip-address $YOUR_IP

# Test database connection
psql -h ${POSTGRES_FQDN} \
  -U adminuser@graintrade-postgres \
  -d graintrade -c "SELECT 1;"

# Test Redis connection
redis-cli -h ${REDIS_HOST} -p 6380 --tls ping

# Test RabbitMQ connection
RABBITMQ_IP=$(az container show --resource-group graintrade-rg --name rabbitmq-container --query ipAddress.ip -o tsv)
RABBITMQ_PASS=$(az keyvault secret show --vault-name graintrade-kv --name rabbitmq-password --query value -o tsv)
# Use connection string: amqp://guest:$RABBITMQ_PASS@$RABBITMQ_IP:5672/
```

## 📊 GitHub Actions

```bash
# Configure secrets for CI/CD
# Go to: GitHub Repo > Settings > Secrets and variables > Actions

# Secrets needed:
# 1. AZURE_CREDENTIALS - JSON from: az ad sp create-for-rbac...
# 2. AZURE_REGISTRY_LOGIN_SERVER - From: terraform output
# 3. AZURE_REGISTRY_USERNAME - From: az acr credential show
# 4. AZURE_REGISTRY_PASSWORD - From: az acr credential show
# 5. AZURE_STATIC_WEB_APPS_TOKEN - For frontend deployment (optional)

# Test pipeline
git add terraform/
git commit -m "test: trigger CI/CD"
git push origin develop

# Monitor: GitHub Repo > Actions tab
```

## 🆘 Troubleshooting Quick Fixes

```bash
# Container won't start?
az webapp log tail --resource-group graintrade-rg --name graintrade-backend --lines 100

# Database connection fails?
psql -h ${POSTGRES_FQDN} -U adminuser@graintrade-postgres -d graintrade -c "SELECT 1;"

# Redis not responding?
redis-cli -h ${REDIS_HOST} -p 6380 --tls ping

# App Service returns 500?
az webapp stop --resource-group graintrade-rg --name graintrade-backend
az webapp start --resource-group graintrade-rg --name graintrade-backend

# Terraform state messed up?
terraform state list
terraform state rm azurerm_resource.id  # Remove problematic resource
terraform plan  # Check what will be recreated

# High costs?
az resource delete --resource-group graintrade-rg --name graintrade-redis --resource-type "Microsoft.Cache/redis"
```

## 📱 Useful Links

- **Azure Portal**: https://portal.azure.com
- **Application Insights**: https://portal.azure.com → Resource Group → appinsights-graintrade
- **Container Registry**: https://portal.azure.com → Resource Group → graintradeacr
- **Key Vault**: https://portal.azure.com → Resource Group → graintrade-kv
- **Cost Analysis**: https://portal.azure.com → Cost Management + Billing

---

**Save this file for quick reference during deployment!**

For complete documentation:
- **Terraform Setup**: See `terraform/README.md`
- **Deployment Steps**: See `AZURE_DEPLOYMENT_GUIDE.md`
- **Architecture & Strategy**: See `AZURE_MIGRATION_GUIDE.md`
