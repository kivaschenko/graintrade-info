variable "resource_group_name" {
  description = "Name of the Azure resource group"
  type        = string
  default     = "graintrade-rg"
}

variable "location" {
  description = "Azure region for resource deployment"
  type        = string
  default     = "westeurope"

  validation {
    condition     = contains(["westeurope", "northeurope", "eastus", "westus"], var.location)
    error_message = "Location must be a valid Azure region."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "storage_account_name" {
  description = "Name of the storage account (must be globally unique, lowercase, 3-24 chars)"
  type        = string
  default     = "graintradesa"

  validation {
    condition     = length(var.storage_account_name) >= 3 && length(var.storage_account_name) <= 24 && can(regex("^[a-z0-9]+$", var.storage_account_name))
    error_message = "Storage account name must be 3-24 lowercase alphanumeric characters."
  }
}

variable "vnet_name" {
  description = "Name of the virtual network"
  type        = string
  default     = "vnet-graintrade"
}

variable "vnet_address_space" {
  description = "Address space for the virtual network"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "key_vault_name" {
  description = "Name of the Key Vault (must be globally unique, 3-24 alphanumeric chars and hyphens)"
  type        = string
  default     = "graintrade-kv"

  validation {
    condition     = length(var.key_vault_name) >= 3 && length(var.key_vault_name) <= 24
    error_message = "Key Vault name must be 3-24 characters."
  }
}

variable "postgres_server_name" {
  description = "Name of the PostgreSQL server"
  type        = string
  default     = "graintrade-postgres"

  validation {
    condition     = can(regex("^[a-z0-9-]{3,63}$", var.postgres_server_name))
    error_message = "PostgreSQL server name must be 3-63 characters with lowercase letters, numbers, and hyphens."
  }
}

variable "postgres_admin_user" {
  description = "PostgreSQL admin username"
  type        = string
  default     = "adminuser"
  sensitive   = true
}

variable "redis_name" {
  description = "Name of the Azure Cache for Redis"
  type        = string
  default     = "graintrade-redis"

  validation {
    condition     = can(regex("^[a-z0-9-]{1,63}$", var.redis_name))
    error_message = "Redis name must be 1-63 characters with lowercase letters, numbers, and hyphens."
  }
}

variable "container_registry_name" {
  description = "Name of the Container Registry (must be globally unique, lowercase, 5-50 chars)"
  type        = string
  default     = "graintradeacr"

  validation {
    condition     = length(var.container_registry_name) >= 5 && length(var.container_registry_name) <= 50 && can(regex("^[a-z0-9]+$", var.container_registry_name))
    error_message = "Container Registry name must be 5-50 lowercase alphanumeric characters."
  }
}

variable "app_service_sku" {
  description = "SKU for App Service Plan"
  type        = string
  default     = "B1"

  validation {
    condition     = contains(["B0", "B1", "B2", "B3", "S1", "S2", "S3"], var.app_service_sku)
    error_message = "App Service SKU must be one of: B0, B1, B2, B3, S1, S2, S3."
  }
}

variable "backend_app_name" {
  description = "Name of the Backend App Service"
  type        = string
  default     = "graintrade-backend"

  validation {
    condition     = can(regex("^[a-z0-9-]{2,60}$", var.backend_app_name))
    error_message = "Backend app name must be 2-60 characters with lowercase letters, numbers, and hyphens."
  }
}

variable "chat_app_name" {
  description = "Name of the Chat Room App Service"
  type        = string
  default     = "graintrade-chat"

  validation {
    condition     = can(regex("^[a-z0-9-]{2,60}$", var.chat_app_name))
    error_message = "Chat app name must be 2-60 characters with lowercase letters, numbers, and hyphens."
  }
}

variable "allowed_ip" {
  description = "IP address allowed for direct database access (your home/office IP)"
  type        = string
  sensitive   = true

  validation {
    condition     = can(regex("^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$", var.allowed_ip))
    error_message = "Allowed IP must be a valid IPv4 address."
  }
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default = {
    project = "graintrade"
    managed_by = "terraform"
  }
}
