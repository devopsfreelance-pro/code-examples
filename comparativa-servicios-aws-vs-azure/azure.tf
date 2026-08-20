# Azure: red virtual + storage account con redundancia geo-replicada
# Servicios: Virtual Network + Blob Storage (equivalentes a VPC + S3 en AWS)

resource "azurerm_resource_group" "main" {
  name     = "demo-comparativa-rg"
  location = "East US"

  tags = {
    project = "comparativa-cloud"
  }
}

resource "azurerm_virtual_network" "main" {
  name                = "demo-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_subnet" "private" {
  name                 = "demo-private-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_storage_account" "demo" {
  name                     = "democomparativastorage"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "GRS" # Geo-redundant storage

  tags = {
    project = "comparativa-cloud"
  }
}
