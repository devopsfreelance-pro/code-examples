# Patrones de diseño para IaC: módulo reutilizable + entornos parametrizados

Código de ejemplo del post [Patrones de Diseño para IaC: Guía Completa 2026](https://www.devopsfreelance.pro/blog/posts/patrones-diseno-iac/).

## Qué demuestra

Implementa en Terraform, de forma ejecutable y sin necesidad de una cuenta
cloud, dos de los patrones centrales del post:

- **Módulos reutilizables**: `modules/network` encapsula el cálculo de
  subredes (con `cidrsubnet`) y la resolución del tamaño de instancia, y
  expone solo los parámetros necesarios (`environment`, `vpc_cidr`, `azs`,
  `instance_sizes`).
- **Entornos parametrizados**: el mismo módulo se reutiliza para
  `development` y `production` sin duplicar código, cambiando únicamente el
  archivo `.tfvars` que se pasa en el `apply` (`dev.tfvars` / `prod.tfvars`),
  igual que el patrón de `variable "instance_sizes"` del post.

Para poder correrlo en cualquier máquina sin credenciales de AWS, el módulo
no crea `aws_vpc` / `aws_subnet` reales: en su lugar escribe el plan de red
resultante (CIDR de cada subred, AZ, tipo de instancia) como un archivo JSON
local con el provider `local`. La lógica de composición y parametrización es
la misma que usarías con recursos reales de AWS.

## Requisitos

- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5
  (no requiere cuenta de AWS ni credenciales; solo usa el provider
  `hashicorp/local`)

## Cómo correrlo

```bash
cd patrones-diseno-iac

# 1. Inicializar (descarga el provider "local")
terraform init

# 2. Desplegar el entorno de desarrollo
terraform apply -var-file=dev.tfvars -auto-approve

# 3. Ver el plan de red generado para "development"
cat output/development-network.json

# 4. Reutilizar el MISMO módulo para producción, sin tocar el código,
#    solo cambiando el tfvars (patrón de entornos parametrizados)
terraform destroy -var-file=dev.tfvars -auto-approve
terraform apply -var-file=prod.tfvars -auto-approve
cat output/production-network.json

# 5. Limpiar
terraform destroy -var-file=prod.tfvars -auto-approve
```

## Salida esperada

Después del paso 2, `terraform apply` termina con algo como:

```
Outputs:

config_file = "./output/development-network.json"
environment = "development"
instance_type = "t3.small"
private_subnets = [
  {
    "az" = "us-east-1a"
    "cidr" = "10.0.0.0/24"
  },
  {
    "az" = "us-east-1b"
    "cidr" = "10.0.1.0/24"
  },
]
```

Y `output/development-network.json` contiene:

```json
{
  "enable_nat_gateway": true,
  "environment": "development",
  "instance_type": "t3.small",
  "private_subnets": [
    { "az": "us-east-1a", "cidr": "10.0.0.0/24" },
    { "az": "us-east-1b", "cidr": "10.0.1.0/24" }
  ],
  "vpc_cidr": "10.0.0.0/16"
}
```

Con `prod.tfvars` el mismo módulo produce `instance_type = "t3.xlarge"` (por
el mapa `instance_sizes` del patrón de entornos parametrizados) y tres
subredes en vez de dos, porque `prod.tfvars` define tres availability zones.

## Estructura

```
patrones-diseno-iac/
├── main.tf                  # raíz: invoca el módulo reutilizable
├── variables.tf              # variables de la raíz + mapa instance_sizes
├── outputs.tf
├── dev.tfvars                 # valores del entorno "development"
├── prod.tfvars                # valores del entorno "production"
└── modules/
    └── network/
        ├── main.tf            # patrón "Módulos Reutilizables"
        ├── variables.tf
        └── outputs.tf
```
