# GrainTrade: Hetzner to AWS Migration Guide

**Date**: January 22, 2026  
**Current Deployment**: Hetzner dedicated server (65.108.68.57)  
**Target Deployment**: AWS ECS + RDS + ElastiCache + Lambda  
**Free Credits**: $200 AWS Promotional Credits  
**Cost Optimization**: Startup phase leveraging free tier and promotional credits

---

## 📊 Executive Summary

This document outlines a comprehensive migration strategy from a Hetzner dedicated server to AWS cloud infrastructure. With $200 in free credits, you can run the entire stack for 2-4 months with minimal out-of-pocket costs.

### Key Advantages of AWS for GrainTrade

1. **Free Tier Benefits**: 12 months of free tier services (RDS, ElastiCache, EC2)
2. **$200 Promotional Credits**: Apply immediately for 2-4 months of free usage
3. **Flexible Scaling**: ECS Fargate for auto-scaling without infrastructure management
4. **Cost Predictability**: Reserved Instances for long-term savings
5. **Global CDN**: CloudFront for frontend delivery
6. **Strong Data Pipeline Support**: Lambda + EventBridge for scheduled tasks

### Cost Comparison

**Current Hetzner Setup:**
- Dedicated server (AMD EPYC 8-core, 32GB RAM, 400GB NVMe): €27/month (~$29 USD)
- Estimated annual cost: **~$348 USD**
- Scaling requires new hardware procurement

**Proposed AWS Setup (Startup Phase - 12-month free tier + $200 credits):**

| Service | Type | Free Tier | Monthly Cost |
|---------|------|-----------|--------------|
| RDS PostgreSQL | db.t3.micro | 12 months, 20GB | $0 (free tier) |
| ElastiCache Redis | cache.t3.micro | 12 months, 1GB | $0 (free tier) |
| ECS Fargate (Backend) | 0.5 vCPU, 1GB | 1M requests/month | $15-20 |
| ECS Fargate (Chat) | 0.5 vCPU, 1GB | 1M requests/month | $15-20 |
| ECS Fargate (Notifications) | 0.5 vCPU, 1GB | Included | $8-10 |
| ECS Fargate (Data Pipeline) | 2 vCPU, 4GB | Included | $20-25 |
| S3 Storage | Standard | 5GB free for 12 months | $0 (free tier) |
| CloudFront | - | 1TB/month free for 12 months | $0 (free tier) |
| NAT Gateway | - | Not free, use ALB | $15-20 |
| Application Load Balancer | - | Partial free tier | $10-15 |
| VPC Endpoints | - | Included in compute | $0 |

**Year 1 Costs:**
- **Months 1-12**: ~$68-90/month with free tier + $200 credits = **$0 out-of-pocket**
- **After free tier expires (Year 2)**: ~$200-250/month

**12-month comparison**:
- Hetzner: $348/year (fixed, no scaling)
- AWS Year 1: $0 (with free tier + credits)
- AWS Year 2: ~$2,400/year (but with auto-scaling capability)

**Break-even analysis**: AWS becomes cheaper after month 8-10 when considering Hetzner's inability to scale cost-effectively.

---

## 🏗️ Current Architecture Analysis

### Services Overview

| Service | Framework | Language | Port | Purpose |
|---------|-----------|----------|------|---------|
| **Backend API** | FastAPI | Python 3.12 | 8000 | Main business logic, user management, data queries |
| **Chat Room** | FastAPI | Python 3.12 | 8001 | Real-time chat functionality with WebSocket |
| **Notifications** | FastAPI | Python 3.12 | 8002 | Email/SMS notifications, alert management |
| **Data Pipeline** | FastAPI | Python 3.12 | 8004 | Market data ingestion, Spark ETL, Delta Lake |
| **Landing Service** | Flask | Python | 8003 | Static landing page, SEO-optimized |
| **Frontend** | Vue.js 3 | JavaScript | 3000 | User interface, real-time updates |
| **PostgreSQL** | - | SQL | 5432 | Primary application database |
| **RabbitMQ** | - | Erlang | 5672 | Message broker for async communication |
| **Redis** | - | C | 6379 | Distributed cache and session storage |

### Current Deployment Architecture

```
User Browser
    ↓
Apache2 (SSL Termination, Reverse Proxy)
    ├── Port 80/443
    ├── Hetzner Dedicated Server
    └── All services on single host
        ├── Backend API (8000)
        ├── Chat Room (8001)
        ├── Notifications (8002)
        ├── Data Pipeline (8004)
        ├── Landing Service (8003)
        ├── Frontend (3000)
        ├── PostgreSQL (5432)
        ├── RabbitMQ (5672)
        └── Redis (6379)
```

### Infrastructure Services

1. **PostgreSQL 16+**: Primary application database with transactions
2. **RabbitMQ**: Message broker for microservice communication and data pipeline tasks
3. **Redis**: Distributed cache, session storage, real-time updates
4. **Apache2**: Reverse proxy with SSL (TLS 1.3)

---

## 🎯 AWS Migration Strategy

### Phase 1: Quick Migration (Week 1-2) - $0 Cost
Deploy to AWS using free tier and promotional credits

**Focus**: Get all services running with minimal configuration
- RDS PostgreSQL (free tier db.t3.micro)
- ElastiCache Redis (free tier cache.t3.micro)
- ECS Fargate for application microservices
- Application Load Balancer for routing
- CloudFront for frontend CDN

**Estimated duration**: 3-5 days
**Cost**: $0 (free tier)

### Phase 2: Optimization (Week 3-4)
Fine-tune performance and implement cost controls

**Focus**: Database optimization, scaling policies, monitoring
- Enable RDS multi-AZ failover (optional)
- Configure ECS auto-scaling policies
- Implement CloudWatch monitoring and alarms
- Set up AWS Backup for RDS

**Estimated duration**: 3-5 days
**Cost**: $0 (still free tier)

### Phase 3: Production Hardening (Week 5-6)
Implement security best practices and disaster recovery

**Focus**: Security, high availability, disaster recovery
- Enable RDS encryption and backups
- Implement VPC security groups and NACLs
- Set up CloudTrail for audit logging
- Configure automated backup retention
- Implement cross-region disaster recovery (optional)

**Estimated duration**: 2-3 days
**Cost**: $5-10/month additional (encryption, extra backups)

### Phase 4: Cost Optimization (Ongoing)
Long-term cost reduction strategies

**Focus**: Reserved Instances, Savings Plans, spot instances
- Purchase 1-year Reserved Instances for RDS
- Consider EC2 Savings Plan for ECS Fargate
- Implement S3 lifecycle policies
- Regular cost analysis and optimization

**Expected savings**: 30-50% reduction in monthly costs

---

## 📋 AWS Resource Mapping

### Architecture: AWS ECS Fargate + Managed Services

```
User Browser (CloudFront CDN)
    ↓
Application Load Balancer (Layer 7)
    ├─── /api/* → Backend API (ECS Fargate Task)
    ├─── /chat/* → Chat Room (ECS Fargate Task)
    ├─── /notify/* → Notifications (ECS Fargate Task)
    ├─── / → Landing Service (Static S3 + CloudFront)
    └─── /app/* → Frontend (Static S3 + CloudFront)
         ↓
    ┌────────────────────────────────────────┐
    │        AWS RDS PostgreSQL              │
    │   (free tier db.t3.micro, 20GB)        │
    └────────────────────────────────────────┘
         ↓
    ┌────────────────────────────────────────┐
    │    AWS ElastiCache Redis               │
    │ (free tier cache.t3.micro, 1GB)        │
    └────────────────────────────────────────┘
         ↑
    EventBridge (Scheduled) ← Data Pipeline Task
    (Triggered every 6 hours)
         ↓
    ECS Task (2 vCPU, 4GB RAM)
    Data Pipeline → Spark ETL
         ↓
    S3 (Delta Lake format)
    RabbitMQ on EC2 (optional)
```

### AWS Service Mapping

| Current Component | AWS Service | Benefits |
|-------------------|-------------|----------|
| PostgreSQL DB | RDS PostgreSQL | Managed backups, auto-patching, multi-AZ failover |
| Redis Cache | ElastiCache | Managed, automatic failover, encryption |
| RabbitMQ | MQ (Managed) or EC2 | MQ is managed; EC2 for cost savings |
| Backend/Chat/Notify | ECS Fargate | Serverless containers, auto-scaling |
| Data Pipeline (scheduled) | ECS + EventBridge | Scheduled tasks with auto-cleanup |
| Frontend/Landing | S3 + CloudFront | Global CDN, automatic caching |
| Reverse Proxy/SSL | ALB + ACM | AWS Certificate Manager (free SSL) |
| Monitoring | CloudWatch | Integrated, auto-dashboards |
| Logs | CloudWatch Logs | Centralized logging, retention policies |
| Secrets | Secrets Manager | Encrypted secret storage |

---

## 🚀 Deployment Architecture Recommendations

### Recommended Approach: ECS Fargate + RDS

**Rationale**: 
- No server management (Fargate is serverless)
- Scales automatically based on demand
- Easy to deploy Docker images
- Cost-effective with auto-scaling
- Perfect for microservices architecture

### Network Architecture

```
AWS VPC (10.0.0.0/16)
│
├── Public Subnet A (10.0.1.0/24)
│   └── Application Load Balancer
│       └── Internet Gateway → 0.0.0.0/0
│
├── Private Subnet B (10.0.2.0/24)
│   ├── ECS Task - Backend
│   ├── ECS Task - Chat Room
│   ├── ECS Task - Notifications
│   └── ECS Task - Data Pipeline
│
├── Private Subnet C (10.0.3.0/24)
│   ├── RDS PostgreSQL (Multi-AZ in production)
│   └── ElastiCache Redis
│
└── NAT Gateway (in public subnet)
    └── Outbound internet access for private subnets

Security Groups:
- ALB Security Group: Inbound 80/443 from 0.0.0.0/0
- ECS Security Group: Inbound from ALB + RabbitMQ SG
- RDS Security Group: Inbound from ECS SG on 5432
- Redis Security Group: Inbound from ECS SG on 6379
- RabbitMQ SG (if EC2): Inbound from ECS SG on 5672
```

---

## 💾 Database Migration Strategy

### Step 1: Pre-Migration Validation

```bash
# On Hetzner server - dump PostgreSQL
pg_dump -h localhost -U postgres -d graintrade > graintrade_dump.sql

# Check dump size and integrity
ls -lh graintrade_dump.sql
wc -l graintrade_dump.sql

# Create S3 bucket for migration
aws s3 mb s3://graintrade-migration-backup-$(date +%s)

# Upload dump to S3
aws s3 cp graintrade_dump.sql s3://graintrade-migration-backup/graintrade_dump.sql
```

### Step 2: Create RDS Instance

```bash
# Create RDS PostgreSQL using AWS CLI or Terraform
aws rds create-db-instance \
  --db-instance-identifier graintrade-postgres \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 16.1 \
  --master-username postgres \
  --master-user-password [SECURE_PASSWORD] \
  --allocated-storage 20 \
  --db-parameter-group-name default.postgres16 \
  --backup-retention-period 7 \
  --multi-az
```

### Step 3: Restore Database

```bash
# Get RDS endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier graintrade-postgres \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)

# Restore from dump
psql -h $RDS_ENDPOINT -U postgres -d graintrade < graintrade_dump.sql

# Verify restoration
psql -h $RDS_ENDPOINT -U postgres -d graintrade -c "\dt"
```

### Step 4: Validate Data Integrity

```bash
# Check table counts
psql -h $RDS_ENDPOINT -U postgres -d graintrade -c \
  "SELECT schemaname, tablename FROM pg_tables WHERE schemaname != 'pg_catalog'"

# Verify key tables
psql -h $RDS_ENDPOINT -U postgres -d graintrade -c "SELECT COUNT(*) FROM users;"
psql -h $RDS_ENDPOINT -U postgres -d graintrade -c "SELECT COUNT(*) FROM commodities;"
```

---

## 🐳 Docker Image Preparation

### Prerequisites

1. AWS Account with $200 credits applied
2. IAM user with permissions for ECR, ECS, RDS, ElastiCache
3. AWS CLI configured locally
4. Docker installed and running

### Build and Push Docker Images

```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name graintrade-backend --region us-east-1
aws ecr create-repository --repository-name graintrade-chat --region us-east-1
aws ecr create-repository --repository-name graintrade-notifications --region us-east-1
aws ecr create-repository --repository-name graintrade-pipeline --region us-east-1

# 2. Get ECR login token
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin [ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com

# 3. Build and tag images
cd backend && \
docker build -t graintrade-backend:latest . && \
docker tag graintrade-backend:latest [ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com/graintrade-backend:latest && \
docker push [ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com/graintrade-backend:latest

# Repeat for chat, notifications, and pipeline services
```

---

## 🔧 AWS ECS Task Definition Examples

### Backend Service - Task Definition

```json
{
  "family": "graintrade-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "[ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com/graintrade-backend:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://postgres:password@graintrade-postgres.c9akciq32.us-east-1.rds.amazonaws.com:5432/graintrade"
        },
        {
          "name": "REDIS_URL",
          "value": "redis://graintrade-redis.abc123.ng.0001.use1.cache.amazonaws.com:6379"
        },
        {
          "name": "RABBITMQ_URL",
          "value": "amqp://user:pass@graintrade-mq.abc123.mq.us-east-1.amazonaws.com:5672"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/graintrade-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

---

## 📊 AWS Management Console Quick Setup

### 1. Launch RDS PostgreSQL

```
AWS Management Console → RDS → Create Database
├── Engine: PostgreSQL 16.1
├── Instance: db.t3.micro (free tier eligible)
├── Database name: graintrade
├── Username: postgres
├── Password: [secure password]
├── Storage: 20 GB SSD
├── Backup retention: 7 days
├── Multi-AZ: Yes
├── Encryption: AES-256
└── Monitoring: Enable CloudWatch
```

### 2. Launch ElastiCache Redis

```
AWS Management Console → ElastiCache → Create Cluster
├── Engine: Redis 7.x
├── Node type: cache.t3.micro (free tier eligible)
├── Number of nodes: 1
├── Automatic failover: Disabled (for single node)
├── Encryption at rest: Enabled
├── Encryption in transit: Enabled
├── Subnet group: Create new
└── Security group: Allow ECS security group
```

### 3. Create ECS Cluster

```
AWS Management Console → ECS → Create Cluster
├── Cluster name: graintrade-cluster
├── Infrastructure: AWS Fargate
├── Monitoring: Container Insights (optional)
└── Logging: CloudWatch
```

### 4. Create Application Load Balancer

```
AWS Management Console → EC2 → Load Balancers → Create ALB
├── Name: graintrade-alb
├── Scheme: Internet-facing
├── VPC: Select VPC
├── Availability Zones: Select 2+ zones
├── Security Group: Allow 80, 443, 8000-8002
├── Listener: HTTP 80 → Target Group
└── TLS Certificate: AWS Certificate Manager (free)
```

---

## 💰 Cost Optimization Strategies

### 1. Maximize Free Tier Usage (Months 1-12)

```
RDS:           $0  (db.t3.micro, 20GB, 12 months)
ElastiCache:   $0  (cache.t3.micro, 1GB, 12 months)
S3:            $0  (5GB, 12 months)
CloudFront:    $0  (1TB/month, 12 months)
Lambda:        $0  (1M invocations/month)
───────────────────
Total Free:    $0
```

### 2. Apply $200 AWS Promotional Credits

```
Months 1-2:    ~$50/month usage covered by $200 credits
Months 3-4:    Remaining $100 covers 2 more months
Months 5-12:   Additional costs = ~$80/month × 8 = $640

Total Year 1 Cost: $200 (free credits) + $640 (months 5-12) = ~$840
Average/month: ~$70
```

### 3. Purchase Reserved Instances (Month 4)

After experiencing actual usage patterns:

```bash
# 1-year Reserved Instance Commitment (40% savings)
RDS db.t3.micro: ~$60/month → ~$36/month
ElastiCache cache.t3.micro: ~$15/month → ~$9/month
ECS Fargate: ~$80/month → ~$48/month (with Savings Plan)
───────────────────────────────
Monthly savings: ~$22/month = $264/year
```

### 4. Implement Cost Controls

```bash
# Set up AWS Budgets
aws budgets create-budget \
  --account-id [YOUR_ACCOUNT_ID] \
  --budget Name=GrainTrade-Monthly,Type=MONTHLY,Limit=250

# Enable cost anomaly detection
aws ce create-anomaly-monitor \
  --anomaly-monitor '{
    "MonitorName": "GrainTrade-Anomalies",
    "MonitorType": "DIMENSIONAL",
    "MonitorDimension": "SERVICE"
  }'
```

### 5. Right-Size ECS Tasks

Start small and adjust based on monitoring:

```
Initial:  0.25 vCPU × 512 MB    → $8/month
Monitor utilization for 2 weeks
Adjust:   0.5 vCPU × 1GB        → $15/month
Target:   1.0 vCPU × 2GB        → $30/month (for high traffic)
```

---

## 🔐 Security Best Practices

### 1. Secrets Management

```bash
# Store sensitive data in AWS Secrets Manager
aws secretsmanager create-secret \
  --name graintrade/database/password \
  --secret-string '{"username":"postgres","password":"[SECURE]"}'

# Retrieve in ECS task
aws secretsmanager get-secret-value \
  --secret-id graintrade/database/password
```

### 2. RDS Security

```
✓ Enable encryption at rest (AWS KMS)
✓ Enable encryption in transit (SSL/TLS)
✓ Enable automated backups (7-day retention)
✓ Enable Multi-AZ deployment
✓ Restrict security group to ECS tasks only
✓ Change master password immediately
✓ Enable Enhanced Monitoring
✓ Enable audit logging for compliance
```

### 3. VPC Security

```
✓ Use private subnets for RDS and Redis
✓ Implement NACLs (Network ACLs)
✓ Enable VPC Flow Logs
✓ Use security groups (not open to internet)
✓ Implement least privilege IAM policies
✓ Enable GuardDuty for threat detection
```

### 4. Application Security

```
✓ Enable HTTPS/TLS on ALB (ACM certificate)
✓ Enable WAF on ALB for DDoS protection
✓ Implement rate limiting
✓ Enable CloudTrail for audit logging
✓ Implement VPC endpoint for S3 (no NAT charge)
✓ Enable API Gateway logging
✓ Implement mutual TLS between services
```

---

## 📈 Monitoring & Observability

### CloudWatch Dashboards

```bash
# Create custom dashboard
aws cloudwatch put-dashboard \
  --dashboard-name GrainTrade-Main \
  --dashboard-body file://dashboard.json
```

### Key Metrics to Monitor

```
ECS Tasks:
├── CPU Utilization (target: 50-70%)
├── Memory Utilization (target: 60-80%)
├── Task Count (desired vs running)
├── Request Count per task
└── Error rates

RDS:
├── CPU Utilization
├── Database Connections
├── Query Performance Insights
├── Storage Used
└── Backup Status

Redis:
├── Cache Hit Rate (target: >80%)
├── Evictions
├── Memory Usage
├── Network bytes in/out
└── Connection count

ALB:
├── Request Count
├── Target Response Time
├── HTTP 4xx/5xx errors
├── Active Connection Count
└── New Connection Count
```

### CloudWatch Alarms

```bash
# High CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name graintrade-backend-high-cpu \
  --alarm-description "Alert if backend CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2

# RDS connection alarm
aws cloudwatch put-metric-alarm \
  --alarm-name graintrade-db-connections \
  --alarm-description "Alert if DB connections > 50" \
  --metric-name DatabaseConnections \
  --namespace AWS/RDS \
  --threshold 50 \
  --comparison-operator GreaterThanThreshold
```

---

## 🔄 CI/CD Pipeline with AWS

### GitHub Actions to AWS CodeDeploy

```yaml
# .github/workflows/deploy-aws.yml
name: Deploy to AWS ECS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_KEY }}
          aws-region: us-east-1

      - name: Login to ECR
        run: |
          aws ecr get-login-password --region us-east-1 | \
            docker login --username AWS --password-stdin ${{ secrets.ECR_REGISTRY }}

      - name: Build and push Docker image
        run: |
          docker build -t ${{ secrets.ECR_REGISTRY }}/graintrade-backend:${{ github.sha }} .
          docker push ${{ secrets.ECR_REGISTRY }}/graintrade-backend:${{ github.sha }}

      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster graintrade-cluster \
            --service graintrade-backend \
            --force-new-deployment
```

---

## 📋 Step-by-Step Migration Checklist

### Week 1: Preparation & Planning

- [ ] Apply AWS $200 promotional credits
- [ ] Create AWS account and set up billing alerts
- [ ] Set up IAM users and permissions
- [ ] Create S3 bucket for migration files
- [ ] Configure AWS CLI locally
- [ ] Review AWS documentation for services

### Week 2: Infrastructure Setup

- [ ] Create VPC and subnets
- [ ] Create RDS PostgreSQL instance
- [ ] Create ElastiCache Redis instance
- [ ] Create ECS cluster
- [ ] Create Application Load Balancer
- [ ] Set up security groups and NACLs
- [ ] Create ECR repositories

### Week 3: Database & Application Migration

- [ ] Dump PostgreSQL from Hetzner
- [ ] Upload dump to S3
- [ ] Restore database to RDS
- [ ] Validate data integrity
- [ ] Update connection strings in code
- [ ] Build Docker images
- [ ] Push images to ECR

### Week 4: Service Deployment

- [ ] Create ECS task definitions
- [ ] Deploy backend service
- [ ] Deploy chat room service
- [ ] Deploy notifications service
- [ ] Configure load balancer routing
- [ ] Test API endpoints
- [ ] Verify database connectivity

### Week 5: Frontend & Optimization

- [ ] Deploy frontend to S3 + CloudFront
- [ ] Configure custom domain with Route 53
- [ ] Enable HTTPS with ACM certificate
- [ ] Set up CloudWatch monitoring
- [ ] Configure auto-scaling policies
- [ ] Run load tests

### Week 6: Production Hardening

- [ ] Enable RDS Multi-AZ failover
- [ ] Enable encryption at rest and in transit
- [ ] Configure backup retention
- [ ] Implement security groups properly
- [ ] Enable audit logging (CloudTrail)
- [ ] Set up disaster recovery procedures
- [ ] Final validation testing

### Week 7: Cutover & Validation

- [ ] Point DNS to AWS ALB
- [ ] Monitor traffic and errors
- [ ] Validate all services
- [ ] Prepare rollback plan
- [ ] Decommission Hetzner server (after validation)

---

## 🔄 Handling RabbitMQ Migration

### Option 1: AWS MQ (Recommended for ease)

```bash
# Create AWS MQ broker
aws mq create-broker \
  --broker-name graintrade-rabbitmq \
  --engine-type RABBITMQ \
  --engine-version 3.11 \
  --host-instance-type mq.t3.micro \
  --publicly-accessible false \
  --users '[{"Username":"graintrade","Password":"[SECURE]"}]'

# Estimated cost: $0.35/day free tier + $0.10/day after
```

### Option 2: Self-Managed on EC2

```bash
# Launch t3.micro EC2 instance
# Install RabbitMQ
# Start rabbitmq-server

# Pros: Lower cost ($0-5/month with free tier)
# Cons: Manual management, backups, updates
```

### Option 3: Docker container in ECS

```bash
# Run RabbitMQ as separate ECS task
# Pros: Fully managed, part of existing infrastructure
# Cons: Requires EBS volume for persistence
```

**Recommendation**: Start with Option 1 (AWS MQ) for simplicity, migrate to Option 3 later for cost savings.

---

## 💾 Backup & Disaster Recovery

### RDS Automated Backups

```bash
# Configure automatic backups
aws rds modify-db-instance \
  --db-instance-identifier graintrade-postgres \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00" \
  --apply-immediately

# Create manual backup
aws rds create-db-snapshot \
  --db-instance-identifier graintrade-postgres \
  --db-snapshot-identifier graintrade-backup-$(date +%Y%m%d)
```

### Cross-Region Disaster Recovery

```bash
# Create RDS read replica in different region
aws rds create-db-instance-read-replica \
  --db-instance-identifier graintrade-postgres-us-west-2 \
  --source-db-instance-identifier graintrade-postgres \
  --region us-west-2

# In case of disaster, promote read replica
aws rds promote-read-replica \
  --db-instance-identifier graintrade-postgres-us-west-2
```

### S3 Backup for Data Pipeline

```bash
# Enable versioning
aws s3api put-bucket-versioning \
  --bucket graintrade-data \
  --versioning-configuration Status=Enabled

# Set up lifecycle policy for cost optimization
aws s3api put-bucket-lifecycle-configuration \
  --bucket graintrade-data \
  --lifecycle-configuration file://lifecycle.json
```

---

## 🎯 Post-Migration Verification

### Functional Testing

```bash
# Test backend API
curl -X GET https://api.graintrade.com/api/health

# Test chat room
curl -X GET https://api.graintrade.com/chat/health

# Test notifications
curl -X GET https://api.graintrade.com/notify/health

# Verify database connectivity
psql -h $RDS_ENDPOINT -U postgres -d graintrade -c "SELECT VERSION();"

# Verify cache
redis-cli -h $REDIS_ENDPOINT PING
```

### Performance Benchmarking

```bash
# Run load test
ab -n 1000 -c 100 https://api.graintrade.com/api/health

# Monitor metrics in CloudWatch
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=graintrade-backend \
  --statistics Average \
  --start-time 2026-02-01T00:00:00Z \
  --end-time 2026-02-01T23:59:59Z \
  --period 3600
```

### Security Validation

```bash
# Verify HTTPS is enforced
curl -i https://api.graintrade.com | grep "Strict-Transport-Security"

# Check security headers
curl -i https://api.graintrade.com | grep "X-Content-Type-Options"

# Verify no sensitive data in logs
aws logs describe-log-groups | grep graintrade
aws logs tail /ecs/graintrade-backend --follow
```

---

## 📚 AWS Resources & Documentation

### Official AWS Documentation

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [RDS PostgreSQL Documentation](https://docs.aws.amazon.com/rds/latest/userguide/CHAP_PostgreSQL.html)
- [ElastiCache Redis Documentation](https://docs.aws.amazon.com/elasticache/latest/userguide/)
- [Application Load Balancer Documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

### AWS Cost Management

- [AWS Cost Calculator](https://calculator.aws/)
- [AWS Pricing Pages](https://aws.amazon.com/pricing/)
- [Reserved Instance Advisor](https://aws.amazon.com/rds/cost-optimization/)
- [AWS Budgets & Cost Anomaly Detection](https://aws.amazon.com/aws-cost-management/)

### Related Services to Consider

- **AWS Lambda**: For data pipeline instead of ECS tasks
- **AWS EventBridge**: For scheduled tasks instead of cron
- **AWS Glue**: For ETL instead of Spark
- **AWS SageMaker**: For machine learning (future)
- **AWS Kendra**: For search (future)

---

## ⚠️ Important Considerations

### 1. Free Tier Limitations

```
❌ NOT included in free tier:
- NAT Gateway ($30-35/month)
- Data transfer out of AWS (first 1GB free, then $0.09/GB)
- VPC endpoint for S3 ($7/month)
- CloudWatch Insights ($0.50 per GB)

✅ Included in free tier:
- RDS db.t3.micro (20GB storage, 750 hours/month)
- ElastiCache cache.t3.micro (1GB cache, 750 hours/month)
- S3 (5GB storage, 20,000 GET requests)
- CloudFront (1TB/month data transfer)
```

### 2. AWS Account Suspension Risk

```
⚠️ AWS may suspend accounts that:
- Exceed free tier limits significantly
- Use instances for prohibited purposes
- Fail to pay after promotional credits expire
- Have payment method on file but payment fails

✓ Mitigate by:
- Setting up billing alerts before limits
- Regularly monitoring CloudWatch
- Keeping payment method current
- Implementing auto-shutdown policies
```

### 3. Regional Selection

```
Recommendation: Use US-EAST-1 (N. Virginia)
✓ Most service availability
✓ Lowest prices in North America
✓ Closest region to most users

Alternative: US-EAST-2 (Ohio) - Same pricing, lower latency for US Midwest
```

### 4. Data Residency & Compliance

```
Consider if you need:
- GDPR compliance → EU regions (eu-central-1)
- HIPAA compliance → Specific AWS regions
- SOC 2 compliance → AWS handles automatically
- Data locality → Choose region accordingly

For GrainTrade: US-EAST-1 is acceptable unless market requires otherwise
```

---

## 🚀 Rollback Plan

### If Migration Fails

```bash
# 1. Immediately revert DNS back to Hetzner
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456 \
  --change-batch file://revert-dns.json

# 2. Monitor Hetzner server for traffic resumption
curl -X GET https://api-old.graintrade.com/api/health

# 3. Gracefully shutdown AWS resources
aws ecs update-service \
  --cluster graintrade-cluster \
  --service graintrade-backend \
  --desired-count 0

# 4. Keep AWS RDS running for data sync if needed
# 5. Post-mortem analysis and retry planning
```

### Estimated Rollback Time: 15-30 minutes

---

## 📞 Support & Next Steps

### Getting Started

1. **Create AWS Account**: https://aws.amazon.com/
2. **Apply promotional credits**: Account → Credits
3. **Set up IAM user**: IAM → Users → Create User
4. **Configure AWS CLI**: `aws configure`
5. **Start with Terraform** (see recommendations below)

### Terraform Implementation

Create `terraform/` directory with:

```
terraform/
├── main.tf          (RDS, ElastiCache, ECS cluster)
├── variables.tf     (Input variables)
├── outputs.tf       (Output values)
├── vpc.tf           (Networking)
├── ecs.tf           (Container orchestration)
└── README.md        (Deployment guide)
```

Example: See [AWS_TERRAFORM_IMPLEMENTATION.md](AWS_TERRAFORM_IMPLEMENTATION.md) (to be created)

### Estimated Timeline

- **Planning & Preparation**: 2-3 days
- **Infrastructure Setup**: 2-3 days
- **Database Migration**: 1-2 days
- **Application Deployment**: 2-3 days
- **Testing & Validation**: 2-3 days
- **Production Cutover**: 1 day

**Total: 10-15 days** to fully migrate and validate

---

## 📝 Summary: AWS vs Hetzner vs Azure

| Aspect | Hetzner | AWS (Year 1) | Azure |
|--------|---------|-----------|-------|
| **Monthly Cost** | €27 (~$29) | $0-80 (free tier + credits) | $100+ |
| **Scalability** | Limited | Excellent | Excellent |
| **Managed Services** | Limited | Excellent | Excellent |
| **Free Tier** | None | 12 months | None |
| **Setup Time** | Fast | 2-3 weeks | 2-3 weeks |
| **Learning Curve** | Low | Medium | Medium |
| **Long-term Cost** | Low | Medium-High | Medium |
| **Global Presence** | Limited | Excellent | Excellent |
| **Support** | Standard | Excellent (AWS support tiers) | Excellent |

**For GrainTrade's use case:**
- **Year 1**: AWS is best (free tier + $200 credits = $0 cost)
- **Year 2+**: Hetzner remains cheapest if no scaling needed
- **Growing app**: AWS becomes the best option

---

**Last Updated**: January 22, 2026  
**Document Version**: 1.0  
**Status**: Ready for Implementation  
**Author**: Migration Planning Team
