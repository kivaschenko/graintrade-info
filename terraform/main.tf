terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.90"
    }
  }

  # Uncomment to use remote state (recommended for production)
  # backend "azurerm" {
  #   resource_group_name  = "graintrade-rg"
  #   storage_account_name = "graintradetfstate"
  #   container_name       = "tfstate"
  #   key                  = "terraform.tfstate"
  # }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = true
    }
  }
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    environment = var.environment
    project     = "graintrade"
  }
}

# Storage Account (for Terraform state and data pipeline results)
resource "azurerm_storage_account" "main" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  https_traffic_only_enabled = true

  tags = {
    environment = var.environment
    project     = "graintrade"
  }
}

resource "azurerm_storage_container" "data_pipeline" {
  name                  = "data-pipeline-results"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Virtual Network
resource "azurerm_virtual_network" "main" {
  name                = var.vnet_name
  address_space       = var.vnet_address_space
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = {
    environment = var.environment
    project     = "graintrade"
  }
}

# Subnets
resource "azurerm_subnet" "app_service" {
  name                 = "subnet-app-service"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]

  service_endpoints = ["Microsoft.Storage", "Microsoft.Sql", "Microsoft.CognitiveServices"]

  delegation {
    name = "appservice"

    service_delegation {
      name = "Microsoft.Web/serverFarms"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/action"
      ]
    }
  }
}

resource "azurerm_subnet" "database" {
  name                 = "subnet-database"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.2.0/24"]

  service_endpoints = ["Microsoft.Storage"]
}

resource "azurerm_subnet" "containers" {
  name                 = "subnet-containers"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.3.0/24"]
}

# Network Security Group - App Service
resource "azurerm_network_security_group" "app_nsg" {
  name                = "nsg-app-service"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  security_rule {
    name                       = "AllowHTTPS"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "AllowHTTP"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = {
    environment = var.environment
  }
}

# Key Vault
resource "azurerm_key_vault" "main" {
  name                        = var.key_vault_name
  location                    = azurerm_resource_group.main.location
  resource_group_name         = azurerm_resource_group.main.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "standard"
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false
  enabled_for_disk_encryption = false

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    key_permissions = [
      "Get",
      "Create",
      "Delete",
      "List"
    ]

    secret_permissions = [
      "Get",
      "Set",
      "Delete",
      "List"
    ]

    certificate_permissions = [
      "Get",
      "Create",
      "Delete",
      "List"
    ]
  }

  tags = {
    environment = var.environment
  }
}

# PostgreSQL Flexible Server
resource "azurerm_postgresql_flexible_server" "main" {
  name                   = var.postgres_server_name
  resource_group_name    = azurerm_resource_group.main.name
  location               = azurerm_resource_group.main.location
  version                = "16"
  administrator_login    = var.postgres_admin_user
  administrator_password = random_password.postgres_password.result
  zone                   = "1"

  storage_mb   = 32768 # 32 GB
  sku_name     = "B_Standard_B1ms"

  backup_retention_days = 7
  geo_redundant_backup_enabled = false
  create_mode = "Default"

  tags = {
    environment = var.environment
  }

  depends_on = [azurerm_resource_group.main]
}

# PostgreSQL Flexible Server Virtual Network Rule
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure" {
  name             = "allow-azure-services"
  server_id        = azurerm_postgresql_flexible_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# PostgreSQL Flexible Server Virtual Network Rule
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_home" {
  name             = "allow-home-ip"
  server_id        = azurerm_postgresql_flexible_server.main.id
  start_ip_address = var.allowed_ip
  end_ip_address   = var.allowed_ip
}

# PostgreSQL Database
resource "azurerm_postgresql_flexible_server_database" "graintrade" {
  name      = "graintrade"
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# Store PostgreSQL connection string in Key Vault
resource "azurerm_key_vault_secret" "postgres_connection_string" {
  name         = "database-url"
  value        = "postgresql://${var.postgres_admin_user}:${random_password.postgres_password.result}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/graintrade"
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [
    azurerm_key_vault.main,
    azurerm_postgresql_flexible_server.main
  ]
}

# Azure Cache for Redis
resource "azurerm_redis_cache" "main" {
  name                = var.redis_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  capacity            = 0 # C0 basic tier
  family              = "C"
  sku_name            = "Basic"
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"

  redis_configuration {
    enable_authentication = true
  }

  tags = {
    environment = var.environment
  }
}

# Store Redis connection string in Key Vault
resource "azurerm_key_vault_secret" "redis_connection_string" {
  name         = "redis-url"
  value        = "rediss://:${azurerm_redis_cache.main.primary_access_key}@${azurerm_redis_cache.main.hostname}:6380?ssl=True"
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [
    azurerm_key_vault.main,
    azurerm_redis_cache.main
  ]
}

# Container Registry
resource "azurerm_container_registry" "main" {
  name                = var.container_registry_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true

  tags = {
    environment = var.environment
  }
}

# App Service Plan (Backend & Chat Room)
resource "azurerm_service_plan" "main" {
  name                = "appplan-graintrade"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = var.app_service_sku

  tags = {
    environment = var.environment
  }
}

# Backend App Service
resource "azurerm_linux_web_app" "backend" {
  name                = var.backend_app_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.main.id

  site_config {
    application_stack {
      docker_image_name   = "${azurerm_container_registry.main.login_server}/backend:latest"
      docker_registry_url = "https://${azurerm_container_registry.main.login_server}"
    }

    container_registry_use_managed_identity = true
    health_check_path                       = "/health"
    http2_enabled                           = true

    # Auto-scale settings
    auto_heal_enabled = true
    auto_heal_setting {
      action {
        action_type = "Recycle"
      }
      trigger {
        status_code_range {
          from = 500
          to   = 599
        }
      }
    }
  }

  app_settings = {
    "DOCKER_REGISTRY_SERVER_URL"      = "https://${azurerm_container_registry.main.login_server}"
    "DOCKER_REGISTRY_SERVER_USERNAME" = azurerm_container_registry.main.admin_username
    "DOCKER_REGISTRY_SERVER_PASSWORD" = azurerm_container_registry.main.admin_password
    "DOCKER_ENABLE_CI"                = "true"
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"
  }

  identity {
    type = "SystemAssigned"
  }

  tags = {
    environment = var.environment
  }

  depends_on = [
    azurerm_service_plan.main,
    azurerm_container_registry.main
  ]
}

# Chat Room App Service
resource "azurerm_linux_web_app" "chat_room" {
  name                = var.chat_app_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.main.id

  site_config {
    application_stack {
      docker_image_name   = "${azurerm_container_registry.main.login_server}/chat-room:latest"
      docker_registry_url = "https://${azurerm_container_registry.main.login_server}"
    }

    container_registry_use_managed_identity = true
    health_check_path                       = "/health"
    http2_enabled                           = true

    auto_heal_enabled = true
    auto_heal_setting {
      action {
        action_type = "Recycle"
      }
      trigger {
        status_code_range {
          from = 500
          to   = 599
        }
      }
    }
  }

  app_settings = {
    "DOCKER_REGISTRY_SERVER_URL"      = "https://${azurerm_container_registry.main.login_server}"
    "DOCKER_REGISTRY_SERVER_USERNAME" = azurerm_container_registry.main.admin_username
    "DOCKER_REGISTRY_SERVER_PASSWORD" = azurerm_container_registry.main.admin_password
    "DOCKER_ENABLE_CI"                = "true"
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"
  }

  identity {
    type = "SystemAssigned"
  }

  tags = {
    environment = var.environment
  }

  depends_on = [
    azurerm_service_plan.main,
    azurerm_container_registry.main
  ]
}

# Notifications Container Instance
resource "azurerm_container_group" "notifications" {
  name                = "notifications-container"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"

  container {
    name   = "notifications"
    image  = "${azurerm_container_registry.main.login_server}/notifications:latest"
    cpu    = "0.5"
    memory = "1.0"

    ports {
      port     = 8002
      protocol = "TCP"
    }

    environment_variables = {
      "LOG_LEVEL" = "INFO"
    }

    secure_environment_variables = {
      "DATABASE_URL" = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.postgres_connection_string.id})"
      "REDIS_URL"    = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.redis_connection_string.id})"
    }
  }

  image_registry_credential {
    server   = azurerm_container_registry.main.login_server
    username = azurerm_container_registry.main.admin_username
    password = azurerm_container_registry.main.admin_password
  }

  restart_policy = "Always"

  tags = {
    environment = var.environment
  }

  depends_on = [
    azurerm_container_registry.main,
    azurerm_postgresql_flexible_server.main,
    azurerm_redis_cache.main
  ]
}

# RabbitMQ Container Instance (message broker)
resource "azurerm_container_group" "rabbitmq" {
  name                = "rabbitmq-container"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"

  container {
    name   = "rabbitmq"
    image  = "rabbitmq:4.0-management"
    cpu    = "1"
    memory = "2.0"

    ports {
      port     = 5672
      protocol = "TCP"
    }

    ports {
      port     = 15672
      protocol = "TCP"
    }

    environment_variables = {
      "RABBITMQ_DEFAULT_USER" = "guest"
      "RABBITMQ_DEFAULT_PASS" = random_password.rabbitmq_password.result
    }
  }

  restart_policy = "Always"

  tags = {
    environment = var.environment
  }

  depends_on = [
    azurerm_resource_group.main
  ]
}

# Store RabbitMQ password in Key Vault
resource "azurerm_key_vault_secret" "rabbitmq_password" {
  name         = "rabbitmq-password"
  value        = random_password.rabbitmq_password.result
  key_vault_id = azurerm_key_vault.main.id
}

# Data Pipeline Container Instance (scheduled)
resource "azurerm_container_group" "data_pipeline" {
  name                = "data-pipeline-container"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  restart_policy      = "Never"

  container {
    name   = "data-pipeline"
    image  = "${azurerm_container_registry.main.login_server}/data-pipeline:latest"
    cpu    = "2"
    memory = "4.0"

    environment_variables = {
      "LOG_LEVEL"       = "INFO"
      "RUN_FORECAST"    = "true"
      "AZURE_STORAGE_ACCOUNT_NAME" = azurerm_storage_account.main.name
      "AZURE_STORAGE_CONTAINER_NAME" = "data-pipeline-results"
    }

    secure_environment_variables = {
      "DATABASE_URL"              = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.postgres_connection_string.id})"
      "AZURE_STORAGE_ACCOUNT_KEY" = azurerm_storage_account.main.primary_access_key
    }
  }

  image_registry_credential {
    server   = azurerm_container_registry.main.login_server
    username = azurerm_container_registry.main.admin_username
    password = azurerm_container_registry.main.admin_password
  }

  tags = {
    environment = var.environment
  }

  depends_on = [
    azurerm_container_registry.main,
    azurerm_postgresql_flexible_server.main,
    azurerm_storage_account.main
  ]
}

# Application Insights
resource "azurerm_application_insights" "main" {
  name                = "appinsights-graintrade"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "web"

  tags = {
    environment = var.environment
  }
}

# Store Application Insights connection string
resource "azurerm_key_vault_secret" "app_insights" {
  name         = "applicationinsights-connection-string"
  value        = azurerm_application_insights.main.connection_string
  key_vault_id = azurerm_key_vault.main.id
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-analytics-graintrade"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = {
    environment = var.environment
  }
}

# Monitor Diagnostic Setting for App Service
resource "azurerm_monitor_diagnostic_setting" "backend" {
  name                       = "diag-backend"
  target_resource_id         = azurerm_linux_web_app.backend.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  enabled_log {
    category = "AppServiceHTTPLogs"
  }

  enabled_log {
    category = "AppServiceConsoleLogs"
  }

  metric {
    category = "AllMetrics"
    enabled  = true
  }
}

# Monitor Alert Rule - Backend CPU High
resource "azurerm_monitor_metric_alert" "backend_cpu_high" {
  name                = "alert-backend-cpu-high"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.backend.id]
  description         = "Alert when backend CPU is high"
  severity            = 2

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "CpuPercentage"
    operator         = "GreaterThan"
    threshold        = 80
    aggregation      = "Average"
  }

  window_size        = "PT5M"
  evaluation_frequency = "PT1M"
}

# Monitor Alert Rule - Backend Response Time High
resource "azurerm_monitor_metric_alert" "backend_response_time" {
  name                = "alert-backend-response-time"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.backend.id]
  description         = "Alert when response time is high"
  severity            = 3

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "AverageResponseTime"
    operator         = "GreaterThan"
    threshold        = 5 # 5 seconds
    aggregation      = "Average"
  }

  window_size        = "PT5M"
  evaluation_frequency = "PT1M"
}

# Data source for current Azure subscription/account
data "azurerm_client_config" "current" {}

# Random passwords for PostgreSQL and RabbitMQ
resource "random_password" "postgres_password" {
  length  = 32
  special = true
}

resource "random_password" "rabbitmq_password" {
  length  = 32
  special = true
}

# Store generated password in Key Vault
resource "azurerm_key_vault_secret" "postgres_password" {
  name         = "postgres-admin-password"
  value        = random_password.postgres_password.result
  key_vault_id = azurerm_key_vault.main.id
}
