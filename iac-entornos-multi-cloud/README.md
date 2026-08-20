# IaC en entornos multi-cloud: ejemplo ejecutable

Post: [IaC multi-cloud: Guía práctica para infraestructura unificada](https://www.devopsfreelance.pro/blog/posts/iac-entornos-multi-cloud/)

## Qué demuestra este ejemplo

El post explica los tres pilares de IaC multi-cloud con Terraform: providers
por nube, abstracción mediante módulos reutilizables, y una estrategia de
naming/tagging consistente que se adapta a las restricciones de cada
proveedor (AWS admite guiones, Azure no admite guiones en varios recursos,
GCP exige minúsculas).

Este ejemplo reproduce exactamente ese patrón con un módulo `network`
declarado tres veces (`aws`, `azure`, `gcp`) desde un único `main.tf`. Cada
submódulo:

- normaliza el nombre del recurso según las reglas de su proveedor,
- arma el mapa de tags comunes (`Project`, `Environment`, `ManagedBy`),
- y en vez de crear un recurso real en la nube (lo que exigiría credenciales
  de AWS/Azure/GCP), escribe un archivo `local_file` en `.output/` que
  simula el "plan de despliegue" con el nombre y los tags ya resueltos.

Así se puede correr `terraform apply` en minutos, sin cuenta cloud y sin
gastar un centavo, y ver el resultado concreto de la abstracción multi-cloud
que describe el post. Para ir a producción real, cada `resource "local_file"
"plan"` se reemplazaría por el recurso nativo (`aws_vpc`, `azurerm_virtual_network`,
`google_compute_network`) manteniendo la misma interfaz de variables.

## Requisitos

- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5.0
- No se necesita cuenta de AWS, Azure ni GCP (el ejemplo solo usa el
  provider `local` de Terraform, que escribe archivos en disco)

## Pasos para correrlo

```bash
cd iac-entornos-multi-cloud
terraform init
terraform apply -auto-approve
```

Ver el resumen con los nombres normalizados y tags por proveedor:

```bash
terraform output resumen_multi_cloud
```

Ver los "planes" de despliegue generados por cada módulo:

```bash
cat .output/aws-production-network.json
cat .output/azure-production-network.json
cat .output/gcp-production-network.json
```

Limpiar todo lo generado:

```bash
terraform destroy -auto-approve
```

## Salida esperada

`terraform output resumen_multi_cloud` debe mostrar algo similar a:

```
{
  "aws" = {
    "name" = "demo-production-network"
    "tags" = {
      "Environment" = "production"
      "ManagedBy" = "terraform"
      "Project" = "demo"
      "Provider" = "aws"
    }
  }
  "azure" = {
    "name" = "demoproductionnetwork"
    "tags" = {
      "Environment" = "production"
      "ManagedBy" = "terraform"
      "Project" = "demo"
      "Provider" = "azure"
    }
  }
  "gcp" = {
    "name" = "demo-production-network"
    "tags" = {
      "Environment" = "production"
      "ManagedBy" = "terraform"
      "Project" = "demo"
      "Provider" = "gcp"
    }
  }
}
```

Notar la diferencia clave: el mismo `base_name` (`demo-production-network`)
se normaliza distinto en Azure (sin guiones) que en AWS/GCP, tal como
describe el post en la sección de naming y tagging.

## Variables personalizables

Se pueden sobreescribir `project` y `environment` al aplicar:

```bash
terraform apply -auto-approve -var="project=acme" -var="environment=staging"
```

## Ir más allá (fuera del alcance de este mini-ejemplo)

El post también cubre el backend de estado remoto en S3 con DynamoDB para
bloqueo. Ese fragmento requiere un bucket S3 y una tabla DynamoDB reales, por
lo que no se incluye en este ejemplo ejecutable localmente. Referencia (no
ejecutar sin adaptar `bucket`, `region` y `dynamodb_table` a recursos
propios):

```hcl
terraform {
  backend "s3" {
    bucket         = "empresa-terraform-state"
    key            = "multi-cloud/production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```
