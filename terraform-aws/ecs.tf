# ECS Cluster and Task Definitions

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.app_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.app_name}-cluster"
  }
}

# ECS Cluster Capacity Providers
resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}

# ==================== TASK DEFINITIONS ====================

# Backend Task Definition
resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.app_name}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([{
    name      = "backend"
    image     = "${aws_ecr_repository.backend.repository_url}:latest"
    essential = true
    portMappings = [{
      containerPort = 8000
      hostPort      = 8000
      protocol      = "tcp"
    }]

    environment = [
      {
        name  = "ENVIRONMENT"
        value = var.environment
      },
      {
        name  = "LOG_LEVEL"
        value = "INFO"
      }
    ]

    secrets = [
      {
        name      = "DATABASE_URL"
        valueFrom = "${aws_secretsmanager_secret.db_password.arn}:database_url::"
      },
      {
        name      = "REDIS_URL"
        valueFrom = "${aws_secretsmanager_secret.redis_auth.arn}:redis_url::"
      },
      {
        name      = "RABBITMQ_URL"
        valueFrom = "${aws_secretsmanager_secret.rabbitmq.arn}:rabbitmq_url::"
      }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "backend"
      }
    }
  }])

  tags = {
    Name = "${var.app_name}-backend-task"
  }
}

# Chat Room Task Definition
resource "aws_ecs_task_definition" "chat" {
  family                   = "${var.app_name}-chat"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([{
    name      = "chat"
    image     = "${aws_ecr_repository.chat.repository_url}:latest"
    essential = true
    portMappings = [{
      containerPort = 8001
      hostPort      = 8001
      protocol      = "tcp"
    }]

    environment = [
      {
        name  = "ENVIRONMENT"
        value = var.environment
      },
      {
        name  = "LOG_LEVEL"
        value = "INFO"
      }
    ]

    secrets = [
      {
        name      = "DATABASE_URL"
        valueFrom = "${aws_secretsmanager_secret.db_password.arn}:database_url::"
      },
      {
        name      = "REDIS_URL"
        valueFrom = "${aws_secretsmanager_secret.redis_auth.arn}:redis_url::"
      },
      {
        name      = "RABBITMQ_URL"
        valueFrom = "${aws_secretsmanager_secret.rabbitmq.arn}:rabbitmq_url::"
      }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "chat"
      }
    }
  }])

  tags = {
    Name = "${var.app_name}-chat-task"
  }
}

# Notifications Task Definition
resource "aws_ecs_task_definition" "notifications" {
  family                   = "${var.app_name}-notifications"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([{
    name      = "notifications"
    image     = "${aws_ecr_repository.notifications.repository_url}:latest"
    essential = true
    portMappings = [{
      containerPort = 8002
      hostPort      = 8002
      protocol      = "tcp"
    }]

    environment = [
      {
        name  = "ENVIRONMENT"
        value = var.environment
      },
      {
        name  = "LOG_LEVEL"
        value = "INFO"
      }
    ]

    secrets = [
      {
        name      = "DATABASE_URL"
        valueFrom = "${aws_secretsmanager_secret.db_password.arn}:database_url::"
      },
      {
        name      = "REDIS_URL"
        valueFrom = "${aws_secretsmanager_secret.redis_auth.arn}:redis_url::"
      },
      {
        name      = "RABBITMQ_URL"
        valueFrom = "${aws_secretsmanager_secret.rabbitmq.arn}:rabbitmq_url::"
      }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "notifications"
      }
    }
  }])

  tags = {
    Name = "${var.app_name}-notifications-task"
  }
}

# Data Pipeline Task Definition
resource "aws_ecs_task_definition" "pipeline" {
  family                   = "${var.app_name}-pipeline"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([{
    name      = "pipeline"
    image     = "${aws_ecr_repository.pipeline.repository_url}:latest"
    essential = true

    environment = [
      {
        name  = "ENVIRONMENT"
        value = var.environment
      },
      {
        name  = "LOG_LEVEL"
        value = "INFO"
      },
      {
        name  = "S3_BUCKET"
        value = aws_s3_bucket.data_pipeline.bucket
      }
    ]

    secrets = [
      {
        name      = "DATABASE_URL"
        valueFrom = "${aws_secretsmanager_secret.db_password.arn}:database_url::"
      },
      {
        name      = "REDIS_URL"
        valueFrom = "${aws_secretsmanager_secret.redis_auth.arn}:redis_url::"
      },
      {
        name      = "RABBITMQ_URL"
        valueFrom = "${aws_secretsmanager_secret.rabbitmq.arn}:rabbitmq_url::"
      }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "pipeline"
      }
    }
  }])

  tags = {
    Name = "${var.app_name}-pipeline-task"
  }
}

# ==================== SERVICES ====================

# Backend Service
resource "aws_ecs_service" "backend" {
  name            = "${var.app_name}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.backend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
  }

  depends_on = [aws_lb_listener.http]

  tags = {
    Name = "${var.app_name}-backend-service"
  }
}

# Chat Service
resource "aws_ecs_service" "chat" {
  name            = "${var.app_name}-chat"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.chat.arn
  desired_count   = var.chat_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.chat.arn
    container_name   = "chat"
    container_port   = 8001
  }

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
  }

  depends_on = [aws_lb_listener.http]

  tags = {
    Name = "${var.app_name}-chat-service"
  }
}

# Notifications Service
resource "aws_ecs_service" "notifications" {
  name            = "${var.app_name}-notifications"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.notifications.arn
  desired_count   = var.notifications_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
  }

  tags = {
    Name = "${var.app_name}-notifications-service"
  }
}

# ==================== AUTO SCALING ====================

# Backend Auto Scaling
resource "aws_appautoscaling_target" "backend" {
  max_capacity       = var.backend_max_capacity
  min_capacity       = var.backend_desired_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.backend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "backend_cpu" {
  policy_name        = "${var.app_name}-backend-cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.backend.resource_id
  scalable_dimension = aws_appautoscaling_target.backend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.backend.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value = 70.0
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    scale_out_cooldown  = 300
    scale_in_cooldown   = 300
  }
}

# Chat Auto Scaling
resource "aws_appautoscaling_target" "chat" {
  max_capacity       = var.chat_max_capacity
  min_capacity       = var.chat_desired_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.chat.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "chat_cpu" {
  policy_name        = "${var.app_name}-chat-cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.chat.resource_id
  scalable_dimension = aws_appautoscaling_target.chat.scalable_dimension
  service_namespace  = aws_appautoscaling_target.chat.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value = 70.0
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    scale_out_cooldown  = 300
    scale_in_cooldown   = 300
  }
}
