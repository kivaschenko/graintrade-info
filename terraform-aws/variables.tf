# Terraform Variables for AWS GrainTrade Infrastructure

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"

  validation {
    condition     = contains(["us-east-1", "us-east-2", "us-west-1", "us-west-2"], var.aws_region)
    error_message = "Region must be a valid AWS region."
  }
}

variable "app_name" {
  description = "Application name for resource naming"
  type        = string
  default     = "graintrade"

  validation {
    condition     = length(var.app_name) <= 20 && can(regex("^[a-z0-9-]+$", var.app_name))
    error_message = "App name must be lowercase, alphanumeric, and hyphens only."
  }
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

# ==================== VPC & NETWORKING ====================

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "Must be a valid CIDR block."
  }
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

# ==================== DATABASE ====================

variable "db_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "16.1"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"

  validation {
    condition     = can(regex("^db\\.t[34]\\.", var.db_instance_class))
    error_message = "Instance class must be valid. Use db.t3.* or db.t4.* for free tier compatibility."
  }
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20

  validation {
    condition     = var.db_allocated_storage >= 20 && var.db_allocated_storage <= 1000
    error_message = "Storage must be between 20 and 1000 GB."
  }
}

variable "db_storage_type" {
  description = "Storage type"
  type        = string
  default     = "gp3"

  validation {
    condition     = contains(["gp2", "gp3", "io1"], var.db_storage_type)
    error_message = "Storage type must be gp2, gp3, or io1."
  }
}

variable "db_name" {
  description = "Initial database name"
  type        = string
  default     = "graintrade"
}

variable "db_username" {
  description = "Master username for database"
  type        = string
  default     = "postgres"
  sensitive   = true
}

variable "db_password" {
  description = "Master password for database"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.db_password) >= 8
    error_message = "Password must be at least 8 characters."
  }
}

variable "db_backup_retention" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7

  validation {
    condition     = var.db_backup_retention >= 1 && var.db_backup_retention <= 35
    error_message = "Backup retention must be between 1 and 35 days."
  }
}

variable "enable_multi_az" {
  description = "Enable Multi-AZ deployment for RDS"
  type        = bool
  default     = false
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot on DB deletion"
  type        = bool
  default     = false
}

# ==================== CACHE ====================

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"

  validation {
    condition     = can(regex("^cache\\.t[34]\\.", var.redis_node_type))
    error_message = "Node type must be cache.t3.* or cache.t4.* for free tier compatibility."
  }
}

variable "redis_num_nodes" {
  description = "Number of Redis nodes"
  type        = number
  default     = 1

  validation {
    condition     = var.redis_num_nodes >= 1 && var.redis_num_nodes <= 6
    error_message = "Number of nodes must be between 1 and 6."
  }
}

variable "redis_engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.x"
}

variable "redis_auth_token" {
  description = "Redis auth token"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.redis_auth_token) >= 16
    error_message = "Auth token must be at least 16 characters."
  }
}

variable "redis_automatic_failover" {
  description = "Enable automatic failover"
  type        = bool
  default     = false
}

# ==================== ECR ====================

variable "force_delete_ecr" {
  description = "Force delete ECR repositories"
  type        = bool
  default     = false
}

# ==================== ECS ====================

variable "backend_desired_count" {
  description = "Desired number of backend tasks"
  type        = number
  default     = 1

  validation {
    condition     = var.backend_desired_count >= 1 && var.backend_desired_count <= 5
    error_message = "Desired count must be between 1 and 5."
  }
}

variable "backend_max_capacity" {
  description = "Maximum number of backend tasks for auto-scaling"
  type        = number
  default     = 3

  validation {
    condition     = var.backend_max_capacity >= 1 && var.backend_max_capacity <= 10
    error_message = "Max capacity must be between 1 and 10."
  }
}

variable "chat_desired_count" {
  description = "Desired number of chat tasks"
  type        = number
  default     = 1

  validation {
    condition     = var.chat_desired_count >= 1 && var.chat_desired_count <= 5
    error_message = "Desired count must be between 1 and 5."
  }
}

variable "chat_max_capacity" {
  description = "Maximum number of chat tasks for auto-scaling"
  type        = number
  default     = 3

  validation {
    condition     = var.chat_max_capacity >= 1 && var.chat_max_capacity <= 10
    error_message = "Max capacity must be between 1 and 10."
  }
}

variable "notifications_desired_count" {
  description = "Desired number of notification tasks"
  type        = number
  default     = 1

  validation {
    condition     = var.notifications_desired_count >= 1 && var.notifications_desired_count <= 3
    error_message = "Desired count must be between 1 and 3."
  }
}

# ==================== LOGGING ====================

variable "log_retention_days" {
  description = "CloudWatch Logs retention period"
  type        = number
  default     = 7

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention must be a valid CloudWatch Logs value."
  }
}

# ==================== MONITORING ====================

variable "alert_email" {
  description = "Email for CloudWatch alarms"
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.alert_email))
    error_message = "Must be a valid email address."
  }
}

# ==================== RABBITMQ ====================

variable "rabbitmq_username" {
  description = "RabbitMQ username"
  type        = string
  default     = "graintrade"
  sensitive   = true
}

variable "rabbitmq_password" {
  description = "RabbitMQ password"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.rabbitmq_password) >= 8
    error_message = "Password must be at least 8 characters."
  }
}

variable "rabbitmq_host" {
  description = "RabbitMQ host"
  type        = string
  default     = "rabbitmq.example.com"
}

variable "rabbitmq_port" {
  description = "RabbitMQ port"
  type        = number
  default     = 5672

  validation {
    condition     = var.rabbitmq_port > 0 && var.rabbitmq_port < 65536
    error_message = "Port must be between 1 and 65535."
  }
}
