terraform {
  required_version = ">= 1.6"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

# Dos microservicios provisionados a partir del mismo módulo reutilizable,
# tal como se describe en el post para el caso de la startup.
module "api_usuarios" {
  source = "./modules/microservicio"

  nombre_servicio    = "api-usuarios"
  replicas           = 3
  habilitar_metricas = true
  puerto_metricas    = 9090
}

module "api_pagos" {
  source = "./modules/microservicio"

  nombre_servicio    = "api-pagos"
  replicas           = 2
  habilitar_metricas = false
}

output "servicios_generados" {
  value = [
    module.api_usuarios.archivo_generado,
    module.api_pagos.archivo_generado,
  ]
}
