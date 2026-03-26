# GrainTrade AWS Infrastructure - Terraform Guide

## Overview

This Terraform configuration deploys the complete GrainTrade infrastructure on AWS using:

- **ECS Fargate**: Serverless container orchestration
- **RDS PostgreSQL**: Managed relational database
- **ElastiCache Redis**: Managed in-memory cache
- **Application Load Balancer**: Layer 7 load balancing
- **ECR**: Docker image repositories
- **CloudWatch**: Monitoring and logging
- **Secrets Manager**: Secure credential storage

## Prerequisites

### Software Requirements

```bash
# 1. Terraform >= 1.0
terraform --version

# 2. AWS CLI >= 2.0
aws --version

# 3. Docker (for building images)
docker --version
```

### AWS Account Requirements

1. Active AWS account with $200 promotional credits applied
2. IAM user with permissions for:
   - EC2 (VPC, subnets, security groups)
   - RDS (database instances, security groups)
   - ElastiCache (clusters, parameter groups)
   - ECS (clusters, services, task definitions)
   - ECR (repositories)
   - S3 (buckets)
   - IAM (roles, policies)
   - Secrets Manager
   - CloudWatch (logs, alarms)
   - SNS (topics)

3. AWS credentials configured:
   ```bash
   aws configure
   # Enter: AWS Access Key ID
   # Enter: AWS Secret Access Key
   # Enter: Default region (us-east-1)
   # Enter: Default output format (json)
   ```

## File Structure

```
terraform-aws/
├── main.tf                    # Core resources (RDS, ElastiCache, ECR, S3)
├── vpc.tf                     # Networking (VPC, subnets, security groups, ALB)
├── ecs.tf                     # Container orchestration (cluster, services, tasks)
├── variables.tf               # Input variable definitions
├── outputs.tf                 # Output values
├── terraform.tfvars.example   # Example values file
└── README.md                  # This file
```

## Quick Start

### Step 1: Prepare Configuration

```bash
# Navigate to terraform directory
cd terraform-aws

# Copy example values file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

### Step 2: Set Required Variables

Edit `terraform.tfvars` and provide:

```hcl
# REQUIRED - No defaults
alert_email = "your-email@example.com"
db_password = "YourSecurePassword123!"
redis_auth_token = "YourRedisAuthToken1234567890"
rabbitmq_password = "YourRabbitMQPassword123!"

# OPTIONAL - Have sensible defaults
aws_region = "us-east-1"
environment = "prod"
```

### Step 3: Initialize Terraform

```bash
# Download provider plugins
terraform init

# Validate configuration
terraform validate

# Format configuration
terraform fmt -recursive
```

### Step 4: Plan Deployment

```bash
# Review what will be created
terraform plan -out=tfplan

# Review the output for accuracy
```

### Step 5: Apply Configuration

```bash
# Deploy infrastructure
terraform apply tfplan

# Wait for completion (5-10 minutes)
# Note RDS/Redis initialization takes time
```

### Step 6: Verify Deployment

```bash
# Get deployment outputs
terraform output

# Example outputs:
# alb_dns_name = "graintrade-alb-123456.us-east-1.elb.amazonaws.com"
# rds_address = "graintrade-postgres.c9akciq32.us-east-1.rds.amazonaws.com"
# redis_endpoint = "graintrade-redis.abc123.ng.0001.use1.cache.amazonaws.com"
```

## Configuration Details

### Database (RDS PostgreSQL)

**Free Tier Configuration:**
```hcl
db_instance_class    = "db.t3.micro"     # 2 vCPU, 1GB RAM
db_allocated_storage = 20                # 20GB free tier
db_backup_retention  = 7                 # 7 days
enable_multi_az      = false             # Single AZ for dev
```

**Production Configuration:**
```hcl
db_instance_class    = "db.t3.small"     # 2 vCPU, 2GB RAM
db_allocated_storage = 50                # 50GB for growth
db_backup_retention  = 30                # 30 days
enable_multi_az      = true              # Multi-AZ for HA
```

### Cache (ElastiCache Redis)

**Free Tier Configuration:**
```hcl
redis_node_type          = "cache.t3.micro"     # 0.5GB memory
redis_num_nodes          = 1
redis_automatic_failover = false
```

**Production Configuration:**
```hcl
redis_node_type          = "cache.t3.small"     # 1.4GB memory
redis_num_nodes          = 3                    # Multi-node for HA
redis_automatic_failover = true
```

### ECS Services

**Development Configuration:**
```hcl
backend_desired_count  = 1
backend_max_capacity   = 2
chat_desired_count     = 1
chat_max_capacity      = 2
```

**Production Configuration:**
```hcl
backend_desired_count  = 2
backend_max_capacity   = 5
chat_desired_count     = 2
chat_max_capacity      = 5
```

## Building and Pushing Docker Images

### 1. Authenticate with ECR

```bash
# Get login token
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  $(terraform output -raw aws_account_id).dkr.ecr.us-east-1.amazonaws.com
```

### 2. Build Backend Service

```bash
cd ../backend

docker build -t graintrade-backend:latest .

docker tag graintrade-backend:latest \
  $(terraform output -raw ecr_backend_repository_url):latest

docker push $(terraform output -raw ecr_backend_repository_url):latest

cd ../terraform-aws
```

### 3. Build Chat Service

```bash
cd ../chat-room

docker build -t graintrade-chat:latest .

docker tag graintrade-chat:latest \
  $(terraform output -raw ecr_chat_repository_url):latest

docker push $(terraform output -raw ecr_chat_repository_url):latest

cd ../terraform-aws
```

### 4. Build Notifications Service

```bash
cd ../notifications

docker build -t graintrade-notifications:latest .

docker tag graintrade-notifications:latest \
  $(terraform output -raw ecr_notifications_repository_url):latest

docker push $(terraform output -raw ecr_notifications_repository_url):latest

cd ../terraform-aws
```

### 5. Build Data Pipeline Service

```bash
cd ../data-pipeline

docker build -t graintrade-pipeline:latest .

docker tag graintrade-pipeline:latest \
  $(terraform output -raw ecr_pipeline_repository_url):latest

docker push $(terraform output -raw ecr_pipeline_repository_url):latest

cd ../terraform-aws
```

### Automated Script

Create `deploy-images.sh`:

```bash
#!/bin/bash
set -e

AWS_ACCOUNT_ID=$(terraform output -raw aws_account_id)
AWS_REGION=$(terraform output -raw aws_region)
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_REGISTRY

# Build and push each service
for service in backend chat-room notifications data-pipeline; do
  echo "Building $service..."
  cd ../$service
  docker build -t graintrade-${service}:latest .
  docker tag graintrade-${service}:latest $ECR_REGISTRY/graintrade-${service}:latest
  docker push $ECR_REGISTRY/graintrade-${service}:latest
  cd ../terraform-aws
done

echo "All images pushed successfully!"
```

## Monitoring and Management

### View Logs

```bash
# ECS task logs
aws logs tail /ecs/graintrade --follow

# RDS logs
aws logs tail /rds/graintrade --follow

# Redis logs
aws logs tail /aws/elasticache/graintrade/slow-log --follow
```

### Monitor Services

```bash
# View ECS services
aws ecs list-services --cluster graintrade-cluster

# View running tasks
aws ecs list-tasks --cluster graintrade-cluster

# Describe service
aws ecs describe-services \
  --cluster graintrade-cluster \
  --services graintrade-backend
```

### Scale Services

```bash
# Update desired count for backend
aws ecs update-service \
  --cluster graintrade-cluster \
  --service graintrade-backend \
  --desired-count 3
```

## Cost Monitoring

### Set Budget Alarm

```bash
# Set $250/month budget
aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget '{
    "BudgetName": "GrainTrade-Monthly",
    "BudgetType": "MONTHLY",
    "BudgetLimit": {
      "Amount": "250",
      "Unit": "USD"
    }
  }' \
  --notifications-with-subscriptions '[{
    "Notification": {
      "NotificationType": "FORECASTED",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80
    }
  }]'
```

### Track Costs

```bash
# View cost anomalies
aws ce describe-anomaly-detectors

# Get recent costs
aws ce get-cost-and-usage \
  --time-period Start=2026-01-01,End=2026-01-31 \
  --granularity DAILY \
  --metrics BlendedCost
```

## Troubleshooting

### RDS Connection Failed

```bash
# Check security group
aws ec2 describe-security-groups \
  --group-ids $(terraform output -raw rds_security_group_id)

# Test connectivity
psql -h $(terraform output -raw rds_address) \
  -U postgres -d graintrade
```

### ECS Task Failing to Start

```bash
# View task logs
aws ecs describe-tasks \
  --cluster graintrade-cluster \
  --tasks $(aws ecs list-tasks \
    --cluster graintrade-cluster \
    --query taskArns[0] --output text)

# Check logs
aws logs tail /ecs/graintrade/backend --follow
```

### Redis Connection Failed

```bash
# Check Redis status
aws elasticache describe-cache-clusters \
  --cache-cluster-id graintrade-redis

# Test connectivity
redis-cli -h $(terraform output -raw redis_endpoint) PING
```

## Updating Infrastructure

### Modify Variables

```bash
# Edit terraform.tfvars
nano terraform.tfvars

# Plan changes
terraform plan

# Apply changes
terraform apply
```

### Scale Database

```hcl
# In terraform.tfvars
db_instance_class = "db.t3.small"  # Scale up
enable_multi_az   = true            # Enable high availability
```

### Scale ECS Services

```hcl
# In terraform.tfvars
backend_desired_count = 3
backend_max_capacity  = 5
```

## Destroying Infrastructure

### Destroy All Resources

```bash
# Review what will be deleted
terraform plan -destroy

# Delete infrastructure
terraform destroy

# Confirm deletion
# Type: yes
```

### Destroy Specific Resources

```bash
# Destroy only ECS services (keeps RDS/Redis)
terraform destroy -target=aws_ecs_service.backend
```

## Cost Optimization Tips

### 1. Use Spot Instances (Savings: 40-50%)

```hcl
# In ecs.tf, modify service launch type
launch_type = "FARGATE_SPOT"  # Instead of "FARGATE"
```

### 2. Downsize During Off-Hours

```bash
# Create EventBridge rule to scale down at night
aws events put-rule --schedule-expression "cron(0 22 ? * MON-FRI *)"
```

### 3. Reserved Instances (Savings: 30-40%)

After 1 month, purchase 1-year Reserved Instances:

```bash
# Get current usage
aws ce get-reservation-purchase-recommendation \
  --service "AmazonRDS"
```

### 4. Optimize Storage

```hcl
# Use gp3 instead of gp2
db_storage_type = "gp3"

# Enable lifecycle policies (done automatically)
```

## Disaster Recovery

### Backup RDS

```bash
# Automatic backups configured for 7 days
# Manual backup:
aws rds create-db-snapshot \
  --db-instance-identifier graintrade-postgres \
  --db-snapshot-identifier graintrade-backup-manual
```

### Restore RDS

```bash
# From automated backup
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier graintrade-postgres-restored \
  --db-snapshot-identifier graintrade-backup-manual
```

## State Management (Production)

### Enable Remote State (Recommended for Teams)

```bash
# 1. Create S3 bucket for state
aws s3 mb s3://graintrade-terraform-state-$(date +%s)

# 2. Enable versioning
aws s3api put-bucket-versioning \
  --bucket graintrade-terraform-state-xyz \
  --versioning-configuration Status=Enabled

# 3. Create DynamoDB table for locks
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# 4. Uncomment backend in main.tf and update with your bucket name
```

## Additional Resources

- [AWS Terraform Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform Best Practices](https://www.terraform.io/docs/language)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

## Support

For issues:

1. Check CloudWatch Logs
2. Run `terraform validate`
3. Review AWS Console for resource status
4. Check IAM permissions
5. Review security group rules

---

**Last Updated**: January 22, 2026  
**Terraform Version**: >= 1.0  
**AWS Provider Version**: ~> 5.0  
**Status**: Production Ready
