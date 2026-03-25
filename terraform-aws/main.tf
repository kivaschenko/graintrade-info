# GrainTrade AWS Infrastructure - Main Configuration
# Provider configuration and core resources

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration for state management
  # Uncomment and update to enable remote state storage
  # backend "s3" {
  #   bucket         = "graintrade-terraform-state"
  #   key            = "prod/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-locks"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "GrainTrade"
      ManagedBy   = "Terraform"
    }
  }
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# ==================== LOGGING ====================

# CloudWatch Log Group for ECS
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/graintrade"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "graintrade-ecs-logs"
  }
}

# CloudWatch Log Group for RDS
resource "aws_cloudwatch_log_group" "rds" {
  name              = "/rds/graintrade"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "graintrade-rds-logs"
  }
}

# CloudWatch Log Group for Redis
resource "aws_cloudwatch_log_group" "redis_slow_log" {
  name              = "/aws/elasticache/graintrade/slow-log"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "graintrade-redis-slow-log"
  }
}

resource "aws_cloudwatch_log_group" "redis_engine_log" {
  name              = "/aws/elasticache/graintrade/engine-log"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "graintrade-redis-engine-log"
  }
}

# ==================== DATABASE ====================

# RDS PostgreSQL Instance
resource "aws_db_instance" "postgres" {
  identifier            = "${var.app_name}-postgres"
  engine               = "postgres"
  engine_version       = var.db_engine_version
  instance_class       = var.db_instance_class
  allocated_storage    = var.db_allocated_storage
  storage_type         = var.db_storage_type
  storage_encrypted    = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  port     = 5432

  # Security
  publicly_accessible       = false
  vpc_security_group_ids    = [aws_security_group.rds.id]
  db_subnet_group_name      = aws_db_subnet_group.postgres.name
  multi_az                  = var.enable_multi_az

  # Backup and maintenance
  backup_retention_period = var.db_backup_retention
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"
  copy_tags_to_snapshot   = true
  skip_final_snapshot     = var.skip_final_snapshot
  final_snapshot_identifier_prefix = "${var.app_name}-final-snapshot"

  # Logging
  enabled_cloudwatch_logs_exports = ["postgresql"]

  # Performance Insights
  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  tags = {
    Name = "${var.app_name}-postgres"
  }

  depends_on = [aws_db_subnet_group.postgres]
}

# DB Subnet Group
resource "aws_db_subnet_group" "postgres" {
  name       = "${var.app_name}-db-subnet"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.app_name}-db-subnet"
  }
}

# ==================== CACHE ====================

# ElastiCache Redis Cluster
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.app_name}-redis"
  engine               = "redis"
  node_type            = var.redis_node_type
  num_cache_nodes      = var.redis_num_nodes
  parameter_group_name = aws_elasticache_parameter_group.redis.name
  engine_version       = var.redis_engine_version
  port                 = 6379

  # Security
  security_group_ids = [aws_security_group.redis.id]
  subnet_group_name  = aws_elasticache_subnet_group.redis.name

  # Encryption
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  # Backup and maintenance
  automatic_failover_enabled = var.redis_automatic_failover
  maintenance_window         = "sun:05:00-sun:06:00"
  snapshot_retention_limit   = 5
  snapshot_window            = "03:00-05:00"

  # Logging
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_slow_log.name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "slow-log"
  }

  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_engine_log.name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "engine-log"
  }

  tags = {
    Name = "${var.app_name}-redis"
  }

  depends_on = [aws_elasticache_subnet_group.redis]
}

# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${var.app_name}-redis-subnet"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.app_name}-redis-subnet"
  }
}

# ElastiCache Parameter Group
resource "aws_elasticache_parameter_group" "redis" {
  family      = "redis7"
  name        = "${var.app_name}-redis-params"
  description = "Parameter group for GrainTrade Redis"

  # Optimization settings
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }

  tags = {
    Name = "${var.app_name}-redis-params"
  }
}

# ==================== CONTAINER REGISTRY ====================

# ECR Repository for Backend
resource "aws_ecr_repository" "backend" {
  name                 = "${var.app_name}-backend"
  image_tag_mutability = "MUTABLE"
  force_delete         = var.force_delete_ecr

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name = "${var.app_name}-backend-ecr"
  }
}

# ECR Repository for Chat
resource "aws_ecr_repository" "chat" {
  name                 = "${var.app_name}-chat"
  image_tag_mutability = "MUTABLE"
  force_delete         = var.force_delete_ecr

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name = "${var.app_name}-chat-ecr"
  }
}

# ECR Repository for Notifications
resource "aws_ecr_repository" "notifications" {
  name                 = "${var.app_name}-notifications"
  image_tag_mutability = "MUTABLE"
  force_delete         = var.force_delete_ecr

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name = "${var.app_name}-notifications-ecr"
  }
}

# ECR Repository for Data Pipeline
resource "aws_ecr_repository" "pipeline" {
  name                 = "${var.app_name}-pipeline"
  image_tag_mutability = "MUTABLE"
  force_delete         = var.force_delete_ecr

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name = "${var.app_name}-pipeline-ecr"
  }
}

# ECR Lifecycle Policy (keep only 10 latest images)
resource "aws_ecr_lifecycle_policy" "all" {
  for_each = toset([
    aws_ecr_repository.backend.name,
    aws_ecr_repository.chat.name,
    aws_ecr_repository.notifications.name,
    aws_ecr_repository.pipeline.name,
  ])

  repository = each.value

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "any"
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ==================== S3 BUCKET ====================

# S3 Bucket for Data Pipeline Results
resource "aws_s3_bucket" "data_pipeline" {
  bucket = "${var.app_name}-pipeline-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${var.app_name}-pipeline-data"
  }
}

# Enable versioning for S3 bucket
resource "aws_s3_bucket_versioning" "data_pipeline" {
  bucket = aws_s3_bucket.data_pipeline.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable encryption for S3 bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "data_pipeline" {
  bucket = aws_s3_bucket.data_pipeline.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access to S3 bucket
resource "aws_s3_bucket_public_access_block" "data_pipeline" {
  bucket = aws_s3_bucket.data_pipeline.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Lifecycle policy (archive old data)
resource "aws_s3_bucket_lifecycle_configuration" "data_pipeline" {
  bucket = aws_s3_bucket.data_pipeline.id

  rule {
    id     = "archive-old-data"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 180
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }
}

# ==================== SECRETS MANAGER ====================

# Database password secret
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${var.app_name}/database/password"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.app_name}-db-password"
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
    engine   = "postgres"
    host     = aws_db_instance.postgres.address
    port     = 5432
    dbname   = var.db_name
  })
}

# Redis auth token secret
resource "aws_secretsmanager_secret" "redis_auth" {
  name                    = "${var.app_name}/redis/auth"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.app_name}-redis-auth"
  }
}

resource "aws_secretsmanager_secret_version" "redis_auth" {
  secret_id     = aws_secretsmanager_secret.redis_auth.id
  secret_string = jsonencode({
    host = aws_elasticache_cluster.redis.cache_nodes[0].address
    port = 6379
  })
}

# RabbitMQ credentials secret
resource "aws_secretsmanager_secret" "rabbitmq" {
  name                    = "${var.app_name}/rabbitmq/credentials"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.app_name}-rabbitmq-creds"
  }
}

resource "aws_secretsmanager_secret_version" "rabbitmq" {
  secret_id     = aws_secretsmanager_secret.rabbitmq.id
  secret_string = jsonencode({
    username = var.rabbitmq_username
    password = var.rabbitmq_password
    host     = var.rabbitmq_host
    port     = var.rabbitmq_port
  })
}

# ==================== SNS TOPIC FOR ALARMS ====================

# SNS Topic for alarms
resource "aws_sns_topic" "alerts" {
  name = "${var.app_name}-alerts"

  tags = {
    Name = "${var.app_name}-alerts"
  }
}

resource "aws_sns_topic_subscription" "alerts_email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# ==================== MONITORING ALARMS ====================

# CloudWatch Alarm - RDS CPU
resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${var.app_name}-rds-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Alert when RDS CPU exceeds 80%"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.identifier
  }
}

# CloudWatch Alarm - RDS Connections
resource "aws_cloudwatch_metric_alarm" "rds_connections" {
  alarm_name          = "${var.app_name}-rds-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "50"
  alarm_description   = "Alert when RDS connections exceed 50"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.identifier
  }
}

# CloudWatch Alarm - Redis Evictions
resource "aws_cloudwatch_metric_alarm" "redis_evictions" {
  alarm_name          = "${var.app_name}-redis-evictions"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Evictions"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "100"
  alarm_description   = "Alert when Redis evictions exceed 100"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    CacheClusterId = aws_elasticache_cluster.redis.cluster_id
  }
}

# ==================== IAM ROLES ====================

# ECS Task Execution Role
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.app_name}-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.app_name}-ecs-task-execution-role"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Allow access to Secrets Manager and CloudWatch Logs
resource "aws_iam_role_policy" "ecs_task_execution_policy" {
  name = "${var.app_name}-ecs-task-execution-policy"
  role = aws_iam_role.ecs_task_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_secretsmanager_secret.db_password.arn,
          aws_secretsmanager_secret.redis_auth.arn,
          aws_secretsmanager_secret.rabbitmq.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/ecs/*"
      }
    ]
  })
}

# ECS Task Role (application permissions)
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.app_name}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.app_name}-ecs-task-role"
  }
}

# Allow S3 access for data pipeline
resource "aws_iam_role_policy" "ecs_task_s3_policy" {
  name = "${var.app_name}-ecs-task-s3-policy"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_pipeline.arn,
          "${aws_s3_bucket.data_pipeline.arn}/*"
        ]
      }
    ]
  })
}
