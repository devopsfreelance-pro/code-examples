terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Credenciales ficticias: alcanza con "terraform validate" (chequeo de sintaxis y
# esquema), que no llama a ninguna API de AWS/Azure/GCP. No hace falta cuenta real.

provider "aws" {
  region                      = "us-east-1"
  access_key                  = "fake-access-key"
  secret_key                  = "fake-secret-key"
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
}

provider "azurerm" {
  features {}

  skip_provider_registration = true
  subscription_id            = "00000000-0000-0000-0000-000000000000"
  client_id                  = "00000000-0000-0000-0000-000000000000"
  client_secret              = "fake-secret"
  tenant_id                  = "00000000-0000-0000-0000-000000000000"
}

provider "google" {
  project = "demo-project-id"
  region  = "us-central1"
}
