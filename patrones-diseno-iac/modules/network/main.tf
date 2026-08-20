# Módulo de red reutilizable (patrón "Módulos Reutilizables" del post).
#
# Encapsula la lógica de cálculo de subredes y de selección de tamaño de
# instancia por entorno. No crea recursos reales de AWS: en su lugar
# "materializa" el plan de red como un archivo JSON local, para que el
# ejemplo se pueda ejecutar sin cuenta cloud ni credenciales.
#
# En un proyecto real este mismo módulo tendría el bloque anterior
# reemplazado por aws_vpc, aws_subnet, aws_nat_gateway, etc. (ver el
# ejemplo "module vpc_production" del post).

locals {
  instance_type = var.instance_sizes[var.environment]

  # cada AZ recibe un /24 dentro del CIDR de la VPC (subred privada)
  private_subnets = [
    for idx, az in var.azs : {
      az   = az
      cidr = cidrsubnet(var.vpc_cidr, 8, idx)
    }
  ]
}

resource "local_file" "network_config" {
  filename = "${path.root}/output/${var.environment}-network.json"

  content = jsonencode({
    environment        = var.environment
    vpc_cidr           = var.vpc_cidr
    instance_type      = local.instance_type
    enable_nat_gateway = var.enable_nat_gateway
    private_subnets    = local.private_subnets
  })
}
