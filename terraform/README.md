# GrainTrade Terraform Configuration

This directory contains complete Infrastructure-as-Code (IaC) using Terraform to deploy GrainTrade to Azure Cloud.

## 📋 Quick Start

### Prerequisites

1. **Azure Subscription**: https://azure.microsoft.com/
2. **Terraform**: v1.0+ (https://www.terraform.io/downloads)
3. **Azure CLI**: https://docs.microsoft.com/cli/azure/
4. **Git**: For cloning and version control

### Installation

```bash
# 1. Install Azure CLI (if not already installed)
# macOS
brew install azure-cli

# Windows
choco install azure-cli

# Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# 2. Install Terraform
# https://www.terraform.io/downloads

# 3. Verify installations
az --version
terraform --version
```

## 🚀 Deployment Steps

### Step 1: Authenticate to Azure

```bash
# Login to your Azure subscription
az login

# Set the subscription (if you have multiple)
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Verify authentication
az account show
```

### Step 2: Prepare Terraform Variables

```bash
# Copy example configuration
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
# OR
vim terraform.tfvars
```

**Required variables to update:**

- `allowed_ip`: Your public IP address (get it via `curl https://checkip.amazonaws.com`)
- `storage_account_name`: Globally unique name (only lowercase letters/numbers)
- `container_registry_name`: Globally unique name (5-50 chars, lowercase)
- `key_vault_name`: Globally unique name (3-24 chars)
- `postgres_admin_user`: Strong admin username (NOT "admin")

Example `terraform.tfvars`:
```hcl
location = "westeurope"
environment = "prod"
resource_group_name = "graintrade-rg"
storage_account_name = "graintradesa123"  # Must be unique
container_registry_name = "graintradeacr123"  # Must be unique
postgres_server_name = "graintrade-postgres"
postgres_admin_user = "dbadmin"
allowed_ip = "203.0.113.45"  # Your IP address
```

### Step 3: Initialize Terraform

```bash
# Download and initialize provider plugins
terraform init

# Verify configuration
terraform validate

# (Optional) Format configuration files
terraform fmt -recursive
```

### Step 4: Plan Deployment

```bash
# Review what Terraform will create
terraform plan -out=tfplan

# Expected output: ~20+ resources to be created
# Review the plan carefully before proceeding
```

### Step 5: Apply Configuration

```bash
# Deploy to Azure (this will take 15-30 minutes)
terraform apply tfplan

# Or apply directly with confirmation
terraform apply

# Terraform will display outputs with important URLs and credentials
```

The deployment includes:
- ✅ Resource Group
- ✅ Virtual Network with subnets
- ✅ PostgreSQL Flexible Server (15-20 min)
- ✅ Azure Cache for Redis
- ✅ App Service Plan
- ✅ Backend App Service
- ✅ Chat Room App Service
- ✅ Container Registry
- ✅ Notifications Container Instance
- ✅ Data Pipeline Container Instance
- ✅ Key Vault with secrets
- ✅ Application Insights & Log Analytics
- ✅ Network Security Groups
- ✅ Monitor Alerts

### Step 6: Retrieve Outputs

```bash
# View all outputs
terraform output

# View specific output
terraform output backend_app_url
terraform output postgres_server_fqdn
terraform output container_registry_login_server

# Sensitive outputs (requires explicit request)
terraform output postgres_server_fqdn
terraform output key_vault_uri
```

## 📦 Building and Pushing Docker Images

After Terraform completes, build and push your Docker images:

```bash
# Get login credentials
az acr login --name graintradeacr

# Build images
docker build -t graintradeacr.azurecr.io/backend:latest ./backend
docker build -t graintradeacr.azurecr.io/chat-room:latest ./chat-room
docker build -t graintradeacr.azurecr.io/notifications:latest ./notifications
docker build -t graintradeacr.azurecr.io/data-pipeline:latest ./data-pipeline

# Push to Azure Container Registry
docker push graintradeacr.azurecr.io/backend:latest
docker push graintradeacr.azurecr.io/chat-room:latest
docker push graintradeacr.azurecr.io/notifications:latest
docker push graintradeacr.azurecr.io/data-pipeline:latest

# Verify images
az acr repository list --name graintradeacr
```

## 🔐 Configuring App Services

### 1. Set Environment Variables from Key Vault

```bash
# Get PostgreSQL connection string from Key Vault
DB_URL=$(az keyvault secret show --vault-name graintrade-kv --name database-url --query value -o tsv)

# Set for Backend App Service
az webapp config appsettings set --resource-group graintrade-rg --name graintrade-backend \
  --settings \
    DATABASE_URL="$DB_URL" \
    REDIS_URL="$(az keyvault secret show --vault-name graintrade-kv --name redis-url --query value -o tsv)" \
    RABBITMQ_URL="amqp://guest:guest@rabbitmq-hostname:5672/" \
    JWT_SECRET_KEY="your-secret-key" \
    ENVIRONMENT="production"

# Set for Chat App Service
az webapp config appsettings set --resource-group graintrade-rg --name graintrade-chat \
  --settings \
    DATABASE_URL="$DB_URL" \
    REDIS_URL="$(az keyvault secret show --vault-name graintrade-kv --name redis-url --query value -o tsv)" \
    ENVIRONMENT="production"
```

### 2. Enable Managed Identity

```bash
# Get Managed Identity object ID for backend
BACKEND_IDENTITY=$(az webapp identity show --resource-group graintrade-rg --name graintrade-backend --query principalId -o tsv)

# Grant Key Vault access
az keyvault set-policy --name graintrade-kv \
  --object-id "$BACKEND_IDENTITY" \
  --secret-permissions get list
```

### 3. Configure Continuous Deployment (Optional)

```bash
# Enable webhook for automatic redeploy when image is pushed
az webapp deployment container config --name graintrade-backend \
  --resource-group graintrade-rg \
  --enable-continuous-deployment
```

## 📊 Monitoring & Troubleshooting

### View App Service Logs

```bash
# Real-time logs
az webapp log tail --resource-group graintrade-rg --name graintrade-backend

# Download logs
az webapp log download --resource-group graintrade-rg --name graintrade-backend
```

### Monitor Deployment Status

```bash
# Check if app is running
az webapp show --resource-group graintrade-rg --name graintrade-backend --query "state" -o tsv

# View scaling configuration
az appservice plan show --resource-group graintrade-rg --name appplan-graintrade --query "sku"
```

### Database Connection Issues

```bash
# Test PostgreSQL connection from your machine
psql -h graintrade-postgres.postgres.database.azure.com \
  -U adminuser@graintrade-postgres \
  -d graintrade

# Check firewall rules
az postgres flexible-server firewall-rule list --resource-group graintrade-rg --name graintrade-postgres
```

## 🔄 Updating Resources

### Scale App Service

```bash
# Scale up to B2 tier
az appservice plan update --resource-group graintrade-rg \
  --name appplan-graintrade --sku B2

# Scale out (multiple instances)
az appservice plan update --resource-group graintrade-rg \
  --name appplan-graintrade --number-of-workers 2
```

### Update PostgreSQL Tier

```bash
# Scale to next tier (D2s)
az postgres flexible-server update --resource-group graintrade-rg \
  --name graintrade-postgres --sku-name Standard_D2s_v3
```

### Update Terraform Configuration

```bash
# Edit variables in terraform.tfvars
nano terraform.tfvars

# Plan changes
terraform plan -out=tfplan

# Apply changes
terraform apply tfplan
```

## 🧹 Cleanup & Destruction

### Completely Remove All Resources

```bash
# Remove all resources (WARNING: This deletes everything!)
terraform destroy

# Or destroy specific resources
terraform destroy -target azurerm_linux_web_app.backend

# Verify destruction
az group list --query "[?name=='graintrade-rg']"
```

### Estimated costs for cleanup:
- No ongoing charges if all resources are destroyed
- PostgreSQL, Redis, and App Service will stop accruing charges immediately
- Storage account data will be deleted

## 💰 Cost Management

### Monitor Costs

```bash
# View current costs (requires Azure Cost Management)
az costmanagement query --timeframe MonthToDate \
  --type "Usage" \
  --dataset '{"granularity":"Daily","aggregation":{"totalCost":{"name":"PreTaxCost","function":"Sum"}}}' \
  --filter '{"dimensions":{"name":"ResourceGroup","operator":"In","values":["graintrade-rg"]}}'
```

### Cost Optimization Tips

1. **Use Azure Advisor**: https://portal.azure.com/#view/Microsoft_Azure_Expert/AdvisorMenuBlade
2. **Set up Budget Alerts**: In Azure Portal > Cost Management > Budgets
3. **Use Reserved Instances**: If traffic is predictable, save 35%+
4. **Scale down during off-hours**: Use App Service Auto-scale rules
5. **Archive old data**: Move data pipeline results to cool/archive storage

### Estimated Monthly Costs (Baseline)

| Resource | SKU | Monthly Cost |
|----------|-----|--------------|
| App Service (Backend) | B1 | $11 |
| App Service (Chat) | B1 (shared) | $0 |
| PostgreSQL | B1ms (Burstable) | $57 |
| Redis | Basic C0 | $12.50 |
| Container Registry | Basic | $5 |
| Storage | 100 GB | $2.50 |
| App Insights | Basic | $2.50 |
| **Total** | | **~$91/month** |

## 🔐 Security Best Practices

### Post-Deployment Security Checklist

- [ ] Enable Key Vault purge protection: `az keyvault update --name graintrade-kv --enable-purge-protection true`
- [ ] Rotate PostgreSQL admin password monthly
- [ ] Enable Azure DDoS Protection (if budget allows)
- [ ] Set up Azure Security Center alerts
- [ ] Configure WAF rules if using Application Gateway
- [ ] Enable logging for all storage accounts
- [ ] Implement Azure Policy for compliance

### Backup Strategy

```bash
# PostgreSQL automatic backups (7 days retention, included)
# Manual backup before major changes
pg_dump -h graintrade-postgres.postgres.database.azure.com \
  -U adminuser@graintrade-postgres \
  -d graintrade > backup-$(date +%Y%m%d).sql
```

## 📚 Additional Resources

- **Azure Terraform Provider**: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs
- **Terraform Best Practices**: https://www.terraform.io/cloud-docs/guides/recommended-practices
- **Azure Architecture**: https://docs.microsoft.com/en-us/azure/architecture/
- **Troubleshooting**: Check `/terraform/README_TROUBLESHOOTING.md`

## 🤝 Support

For issues:

1. Check Terraform logs: `TF_LOG=DEBUG terraform apply`
2. Verify Azure CLI access: `az account show`
3. Review Azure Portal for resource status
4. Check application logs: `az webapp log tail --resource-group graintrade-rg --name graintrade-backend`

## 📝 Version Control

Store `terraform.tfvars` in:
- **Git**: Add to `.gitignore` (contains sensitive data)
- **Azure Key Vault**: Store secrets and sensitive variables
- **Terraform Cloud/Backend**: For team collaboration and state management

Example `.gitignore`:
```
terraform.tfvars
*.tfstate
*.tfstate.*
.terraform/
.terraform.lock.hcl
```

## 🎯 Next Steps

1. [ ] Complete Terraform deployment
2. [ ] Build and push Docker images to ACR
3. [ ] Configure App Service environment variables
4. [ ] Test connectivity to PostgreSQL and Redis
5. [ ] Deploy frontend to Azure Static Web Apps
6. [ ] Set up GitHub Actions for CI/CD
7. [ ] Configure custom domain and SSL
8. [ ] Set up monitoring dashboards
9. [ ] Test failover and backup procedures
10. [ ] Decommission Hetzner server

---

**Last Updated**: January 20, 2026  
**Terraform Version**: ~> 1.0  
**Azure Provider**: ~> 3.90
