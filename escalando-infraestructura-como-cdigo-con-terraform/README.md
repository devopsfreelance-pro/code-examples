# Escalando infraestructura como código con Terraform

Post: https://www.devopsfreelance.pro/blog/posts/escalando-infraestructura-como-cdigo-con-terraform/

## Qué demuestra este ejemplo

El post explica cómo estructurar Terraform para que la infraestructura escale sin
reescribir código: módulos, tagging consistente y `count`/`for_each` en vez de
recursos copiados a mano. Este ejemplo aplica esa idea a escala mínima: una VPC
con subnets públicas que crecen automáticamente según la lista
`availability_zones` que le pases, usando `count` sobre `aws_subnet.public`.

También incluye las dos prácticas de "mejores prácticas" del post que son
fáciles de verificar en minutos:

- **Validación de variables** (`environment` solo acepta `dev`/`staging`/`production`,
  `vpc_cidr` debe ser un CIDR válido).
- **Tagging consistente** vía `local.common_tags` mezclado con `merge()` en cada
  recurso.

Corre 100% local contra [LocalStack](https://www.localstack.cloud/) (servicios
`ec2`, `iam`, `sts`), sin cuenta de AWS ni costo.

## Requisitos

- Docker + Docker Compose
- Terraform >= 1.0 (`terraform version`)
- curl (para chequear que LocalStack levantó)

## Pasos para correrlo

1. Levantar LocalStack:

   ```bash
   docker compose up -d
   ```

2. Esperar a que el servicio EC2 esté disponible (puede tardar unos segundos):

   ```bash
   until curl -s http://localhost:4566/_localstack/health | grep -q '"ec2": "available"'; do
     sleep 2
   done
   ```

3. Inicializar y aplicar Terraform:

   ```bash
   terraform init
   terraform plan -out=tfplan
   terraform apply tfplan
   ```

4. Ver los outputs (la VPC y las subnets creadas en LocalStack):

   ```bash
   terraform output
   ```

5. Para comprobar el escalamiento automático, agregá una availability zone y
   volvé a aplicar sin tocar `main.tf`:

   ```bash
   terraform apply -var='availability_zones=["us-east-1a","us-east-1b","us-east-1c"]'
   ```

   El plan va a mostrar una tercera subnet nueva (`aws_subnet.public[2]`) porque
   `count = length(var.availability_zones)`.

6. Limpiar todo al terminar:

   ```bash
   terraform destroy -auto-approve
   docker compose down -v
   ```

## Salida esperada

Después del `apply` del paso 3, deberías ver algo como:

```
Apply complete! Resources: 7 added, 0 changed, 0 destroyed.

Outputs:

public_subnet_ids = [
  "subnet-xxxxxxxx",
  "subnet-xxxxxxxx",
]
subnet_count = 2
vpc_id = "vpc-xxxxxxxx"
```

Los IDs son generados por LocalStack en cada corrida, van a variar.

## Notas

- El provider AWS apunta a `http://localhost:4566` (endpoint único de
  LocalStack) con credenciales dummy (`test`/`test`); no se necesita cuenta
  real de AWS.
- Si intentás `terraform apply -var='environment=qa'` vas a ver el error de
  `validation` del post ("El entorno debe ser dev, staging o production"): es
  la comprobación temprana de errores que describe la sección de mejores
  prácticas.
- Este ejemplo no incluye backend remoto (S3 + DynamoDB) ni Auto Scaling Group
  porque LocalStack Community no cubre esos servicios gratis; el post explica
  esas piezas en detalle para un entorno real de AWS.
