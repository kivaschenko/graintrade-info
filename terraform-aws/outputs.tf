# Terraform Outputs

# ==================== GENERAL ====================

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "aws_account_id" {
  description = "AWS account ID"
  value       = data.aws_caller_identity.current.account_id
}

# ==================== VPC ====================

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

# ==================== RDS ====================

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_address" {
  description = "RDS address"
  value       = aws_db_instance.postgres.address
}

output "rds_port" {
  description = "RDS port"
  value       = aws_db_instance.postgres.port
}

output "rds_database_name" {
  description = "RDS database name"
  value       = aws_db_instance.postgres.db_name
}

# ==================== REDIS ====================

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "redis_port" {
  description = "Redis port"
  value       = aws_elasticache_cluster.redis.port
}

# ==================== ECR ====================

output "ecr_backend_repository_url" {
  description = "ECR Backend repository URL"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_chat_repository_url" {
  description = "ECR Chat repository URL"
  value       = aws_ecr_repository.chat.repository_url
}

output "ecr_notifications_repository_url" {
  description = "ECR Notifications repository URL"
  value       = aws_ecr_repository.notifications.repository_url
}

output "ecr_pipeline_repository_url" {
  description = "ECR Pipeline repository URL"
  value       = aws_ecr_repository.pipeline.repository_url
}

# ==================== ALB ====================

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.main.dns_name
}

output "alb_arn" {
  description = "ALB ARN"
  value       = aws_lb.main.arn
}

# ==================== ECS ====================

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "backend_service_name" {
  description = "Backend ECS service name"
  value       = aws_ecs_service.backend.name
}

output "chat_service_name" {
  description = "Chat ECS service name"
  value       = aws_ecs_service.chat.name
}

output "notifications_service_name" {
  description = "Notifications ECS service name"
  value       = aws_ecs_service.notifications.name
}

# ==================== S3 ====================

output "s3_bucket_name" {
  description = "S3 bucket name for data pipeline"
  value       = aws_s3_bucket.data_pipeline.bucket
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.data_pipeline.arn
}

# ==================== SECRETS MANAGER ====================

output "db_secret_arn" {
  description = "Database secret ARN"
  value       = aws_secretsmanager_secret.db_password.arn
}

output "redis_secret_arn" {
  description = "Redis secret ARN"
  value       = aws_secretsmanager_secret.redis_auth.arn
}

output "rabbitmq_secret_arn" {
  description = "RabbitMQ secret ARN"
  value       = aws_secretsmanager_secret.rabbitmq.arn
}

# ==================== LOGS ====================

output "ecs_log_group" {
  description = "ECS CloudWatch log group"
  value       = aws_cloudwatch_log_group.ecs.name
}

output "rds_log_group" {
  description = "RDS CloudWatch log group"
  value       = aws_cloudwatch_log_group.rds.name
}

# ==================== MONITORING ====================

output "sns_topic_arn" {
  description = "SNS topic ARN for alarms"
  value       = aws_sns_topic.alerts.arn
}

# ==================== CONNECTION STRINGS ====================

output "database_connection_string" {
  description = "PostgreSQL connection string (non-sensitive)"
  value       = "postgresql://${var.db_username}@${aws_db_instance.postgres.address}:5432/${var.db_name}"
  sensitive   = false
}

output "redis_connection_string" {
  description = "Redis connection string"
  value       = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379"
}

# ==================== DEPLOYMENT INFO ====================

output "deployment_summary" {
  description = "Deployment summary"
  value = {
    cluster_name     = aws_ecs_cluster.main.name
    alb_endpoint     = aws_lb.main.dns_name
    region           = var.aws_region
    environment      = var.environment
    rds_endpoint     = aws_db_instance.postgres.address
    redis_endpoint   = aws_elasticache_cluster.redis.cache_nodes[0].address
    s3_bucket        = aws_s3_bucket.data_pipeline.bucket
  }
}
