# Offer Parser - Deployment Guide

## Local Development

### Prerequisites
- Python 3.10+
- Poetry
- Docker & Docker Compose (optional)

### Setup

```bash
# 1. Initialize data
python initialize_data.py

# 2. Create environment
cp .env.example .env

# 3. Edit .env (choose LLM provider)
# LLM_PROVIDER=fallback  (fastest, free)
# LLM_PROVIDER=openai    (best accuracy)
# LLM_PROVIDER=anthropic (good accuracy)

# 4. Install dependencies
poetry install

# 5. Run service
python run.py
```

Access API at: http://localhost:8005/docs

---

## Docker Deployment

### Build & Run

```bash
# Build image
docker build -t graintrade-offer-parser:v1.0.0 .

# Run with environment
docker run -p 8005:8005 \
  -e LLM_PROVIDER=fallback \
  graintrade-offer-parser:v1.0.0
```

### Docker Compose

```bash
# Start with Redis
docker-compose up -d

# Check logs
docker-compose logs -f offer-parser

# Stop
docker-compose down
```

---

## AWS ECS Deployment

### 1. Create ECR Repository

```bash
aws ecr create-repository \
  --repository-name graintrade-offer-parser \
  --region us-east-1
```

### 2. Build & Push Image

```bash
# Get login token
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -t graintrade-offer-parser:v1.0.0 .

# Tag for ECR
docker tag graintrade-offer-parser:v1.0.0 \
  123456789.dkr.ecr.us-east-1.amazonaws.com/graintrade-offer-parser:v1.0.0

# Push to ECR
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/graintrade-offer-parser:v1.0.0
```

### 3. Create ECS Task Definition

```json
{
  "family": "graintrade-offer-parser",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "offer-parser",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/graintrade-offer-parser:v1.0.0",
      "portMappings": [
        {
          "containerPort": 8005,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "LLM_PROVIDER",
          "value": "fallback"
        },
        {
          "name": "LOG_LEVEL",
          "value": "info"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/graintrade-offer-parser",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8005/health || exit 1"],
        "interval": 30,
        "timeout": 10,
        "retries": 3,
        "startPeriod": 5
      }
    }
  ]
}
```

### 4. Create ECS Service

```bash
# Create CloudWatch log group
aws logs create-log-group \
  --log-group-name /ecs/graintrade-offer-parser \
  --region us-east-1

# Register task definition
aws ecs register-task-definition \
  --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster graintrade-cluster \
  --service-name offer-parser \
  --task-definition graintrade-offer-parser:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --region us-east-1
```

---

## Kubernetes Deployment

### 1. Create Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: offer-parser
  namespace: graintrade
spec:
  replicas: 2
  selector:
    matchLabels:
      app: offer-parser
  template:
    metadata:
      labels:
        app: offer-parser
    spec:
      containers:
      - name: offer-parser
        image: graintrade-offer-parser:v1.0.0
        ports:
        - containerPort: 8005
        env:
        - name: LLM_PROVIDER
          value: "fallback"
        - name: LOG_LEVEL
          value: "info"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-secrets
              key: api-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8005
          initialDelaySeconds: 5
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8005
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### 2. Create Service

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: offer-parser
  namespace: graintrade
spec:
  selector:
    app: offer-parser
  type: ClusterIP
  ports:
  - port: 8005
    targetPort: 8005
    protocol: TCP
```

### 3. Deploy

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Check status
kubectl get pods -n graintrade
kubectl logs -n graintrade -l app=offer-parser
```

---

## Monitoring & Logging

### CloudWatch (AWS)

```bash
# View logs
aws logs tail /ecs/graintrade-offer-parser --follow

# Set up alerts
aws cloudwatch put-metric-alarm \
  --alarm-name offer-parser-errors \
  --alarm-description "Alert on parser errors" \
  --metric-name Errors \
  --namespace AWS/ECS \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

### Prometheus (Self-hosted)

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'offer-parser'
    static_configs:
      - targets: ['localhost:8005']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Datadog

```bash
DD_AGENT_MAJOR_VERSION=7 \
DD_API_KEY=your_api_key \
DD_SITE=datadoghq.com \
docker run -d --name datadog-agent \
  -e DD_DOCKER_ENABLED=true \
  -v /var/run/docker.sock:/var/run/docker.sock \
  gcr.io/datadoghq/agent:latest
```

---

## Scaling

### Horizontal Scaling

**Docker Compose:**
```bash
# Run 3 instances with load balancer
docker-compose up -d --scale offer-parser=3
```

**ECS:**
```bash
# Set desired count
aws ecs update-service \
  --cluster graintrade-cluster \
  --service offer-parser \
  --desired-count 3
```

**Kubernetes:**
```bash
kubectl scale deployment offer-parser --replicas=3 -n graintrade
```

### Auto-scaling (AWS)

```bash
# Create auto-scaling target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/graintrade-cluster/offer-parser \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 5

# Create scaling policy (CPU-based)
aws application-autoscaling put-scaling-policy \
  --policy-name cpu-scaling \
  --service-namespace ecs \
  --resource-id service/graintrade-cluster/offer-parser \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration "{
    TargetValue=70.0,
    PredefinedMetricSpecification={
      PredefinedMetricType=ECSServiceAverageCPUUtilization
    }
  }"
```

---

## Health Checks & Monitoring

### Health Endpoint

```bash
curl http://localhost:8005/health

{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2026-01-22T10:30:45.123Z",
  "llm_provider": "fallback",
  "redis_connected": true,
  "db_connected": true
}
```

### Performance Metrics

```bash
# Check request latency
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8005/health

# Monitor throughput
ab -n 1000 -c 10 http://localhost:8005/health
```

---

## Backup & Disaster Recovery

### Backup Domain Data

```bash
# Backup data directory
docker cp graintrade-offer-parser:/app/data ./backup/data-$(date +%Y%m%d)

# Restore from backup
docker cp ./backup/data-20260122 graintrade-offer-parser:/app/data
```

### Rollback Strategy

```bash
# Tag new version
docker tag graintrade-offer-parser:v1.0.1 \
  123456789.dkr.ecr.us-east-1.amazonaws.com/graintrade-offer-parser:v1.0.1

# If issues, revert to previous
aws ecs update-service \
  --cluster graintrade-cluster \
  --service offer-parser \
  --force-new-deployment \
  --task-definition graintrade-offer-parser:0  # Previous version
```

---

## Troubleshooting Deployment

### Service won't start

```bash
# Check logs
docker logs graintrade-offer-parser

# Check port is available
lsof -i :8005

# Rebuild image
docker build --no-cache -t graintrade-offer-parser:v1.0.0 .
```

### High latency

```bash
# Check LLM provider
curl http://localhost:8005/status | jq .config.llm_provider

# Switch to fallback if using expensive LLM
# Edit .env: LLM_PROVIDER=fallback
```

### Memory issues

```bash
# Increase container memory limit
# Docker: -m 1024m
# ECS: increase memory in task definition
# K8s: update resources.limits.memory
```

---

## Security

### Network Security

```bash
# Restrict to internal only
docker run -p 127.0.0.1:8005:8005 graintrade-offer-parser

# Or use security groups (AWS)
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxx \
  --protocol tcp \
  --port 8005 \
  --source-security-group sg-backend
```

### Secrets Management

```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name graintrade/openai-key \
  --secret-string sk-xxxx

# Reference in ECS task definition
"secrets": [{
  "name": "OPENAI_API_KEY",
  "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:graintrade/openai-key"
}]
```

---

## Cost Optimization

### Resource Allocation

**Development:**
- CPU: 0.25 (256 CPU units)
- Memory: 512 MB
- Replicas: 1

**Production:**
- CPU: 0.5 (512 CPU units)
- Memory: 1024 MB
- Replicas: 2–3

**Estimated Monthly Cost (AWS ECS):**
- 1 task (0.5 CPU, 1GB): ~$15
- 2 tasks: ~$30
- Data transfer: ~$2–5

---

## Version Management

```bash
# Tag and release
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0

# Build specific version
docker build -t graintrade-offer-parser:v1.0.0 .

# Push to registry
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/graintrade-offer-parser:v1.0.0
```

---

**Status:** Ready to deploy  
**Last Updated:** January 22, 2026
