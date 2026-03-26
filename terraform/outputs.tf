output "resource_group_id" {
  description = "ID of the created resource group"
  value       = azurerm_resource_group.main.id
}

output "resource_group_name" {
  description = "Name of the created resource group"
  value       = azurerm_resource_group.main.name
}

output "backend_app_url" {
  description = "URL of the Backend App Service"
  value       = "https://${azurerm_linux_web_app.backend.default_hostname}"
}

output "chat_app_url" {
  description = "URL of the Chat Room App Service"
  value       = "https://${azurerm_linux_web_app.chat_room.default_hostname}"
}

output "backend_app_name" {
  description = "Name of the Backend App Service"
  value       = azurerm_linux_web_app.backend.name
}

output "chat_app_name" {
  description = "Name of the Chat Room App Service"
  value       = azurerm_linux_web_app.chat_room.name
}

output "postgres_server_fqdn" {
  description = "FQDN of the PostgreSQL server"
  value       = azurerm_postgresql_flexible_server.main.fqdn
  sensitive   = true
}

output "postgres_server_name" {
  description = "Name of the PostgreSQL server"
  value       = azurerm_postgresql_flexible_server.main.name
}

output "postgres_database_name" {
  description = "Name of the PostgreSQL database"
  value       = azurerm_postgresql_flexible_server_database.graintrade.name
}

output "redis_hostname" {
  description = "Hostname of the Redis cache"
  value       = azurerm_redis_cache.main.hostname
  sensitive   = true
}

output "redis_port" {
  description = "Port of the Redis cache"
  value       = azurerm_redis_cache.main.port
}

output "rabbitmq_hostname" {
  description = "Hostname of the RabbitMQ container"
  value       = try(azurerm_container_group.rabbitmq.ip_address, "rabbitmq-container.internal")
  sensitive   = true
}

output "rabbitmq_port" {
  description = "Port of the RabbitMQ service"
  value       = 5672
}

output "rabbitmq_management_port" {
  description = "Port of the RabbitMQ management UI"
  value       = 15672
}

output "rabbitmq_username" {
  description = "RabbitMQ default username"
  value       = "guest"
  sensitive   = true
}

output "rabbitmq_password" {
  description = "RabbitMQ default password (stored in Key Vault)"
  value       = "See Key Vault: rabbitmq-password secret"
  sensitive   = true
}

output "container_registry_login_server" {
  description = "Login server of the container registry"
  value       = azurerm_container_registry.main.login_server
}

output "container_registry_admin_username" {
  description = "Admin username of the container registry"
  value       = azurerm_container_registry.main.admin_username
  sensitive   = true
}

output "key_vault_id" {
  description = "ID of the Key Vault"
  value       = azurerm_key_vault.main.id
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

output "storage_account_id" {
  description = "ID of the storage account"
  value       = azurerm_storage_account.main.id
}

output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.main.name
}

output "app_insights_instrumentation_key" {
  description = "Instrumentation key for Application Insights"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

output "log_analytics_workspace_id" {
  description = "ID of the Log Analytics workspace"
  value       = azurerm_log_analytics_workspace.main.id
}

output "vnet_id" {
  description = "ID of the virtual network"
  value       = azurerm_virtual_network.main.id
}

output "notifications_container_ip" {
  description = "IP address of the notifications container"
  value       = try(azurerm_container_group.notifications.ip_address, "N/A")
  sensitive   = true
}

output "data_pipeline_container_id" {
  description = "ID of the data pipeline container"
  value       = azurerm_container_group.data_pipeline.id
}

output "deployment_summary" {
  description = "Summary of deployed resources"
  value = {
    resource_group = azurerm_resource_group.main.name
    region         = azurerm_resource_group.main.location
    backend_service = azurerm_linux_web_app.backend.name
    chat_service   = azurerm_linux_web_app.chat_room.name
    database       = azurerm_postgresql_flexible_server.main.fqdn
    redis          = azurerm_redis_cache.main.hostname
    rabbitmq       = try(azurerm_container_group.rabbitmq.ip_address, "See Azure Portal")
    container_registry = azurerm_container_registry.main.name
  }
  sensitive = true
}
