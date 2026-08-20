# Terraform Modules: reutilización de infraestructura

Ejemplo del post [Terraform Modules: Guía Definitiva para Reutilización](https://www.devopsfreelance.pro/blog/posts/terraform-modules-reutilizacion/).

## Qué demuestra

Un módulo Terraform (`modules/vpc-network`) que crea una VPC con subnets públicas
e Internet Gateway, tal como aparece en el post. El módulo se invoca **dos veces**
desde el root module (`main.tf`) con distintos parámetros (`dev` y `prod`), mostrando
en la práctica el punto central del artículo: un mismo módulo parametrizado, con
variables validadas y outputs bien definidos, se reutiliza para levantar entornos
distintos sin duplicar código HCL.

Para poder ejecutarlo en minutos sin cuenta de AWS ni costo, el provider `aws` apunta
a [LocalStack](https://www.localstack.cloud/) corriendo en Docker en vez de a AWS real.

## Requisitos

- Docker y Docker Compose
- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5.0
- `curl` (para el healthcheck manual, opcional)

## Pasos para ejecutarlo

1. Levantar LocalStack:

```bash
docker compose up -d
```

2. Esperar a que el servicio esté healthy (unos 10-20 segundos):

```bash
until curl -sf http://localhost:4566/_localstack/health | grep -q '"ec2": "available"'; do
  echo "esperando LocalStack..."
  sleep 2
done
```

3. Inicializar y aplicar Terraform:

```bash
terraform init
terraform apply -auto-approve
```

4. Verificar los outputs:

```bash
terraform output
```

5. (Opcional) Verificar directamente contra LocalStack con la CLI de AWS apuntando al
   endpoint local:

```bash
aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs \
  --query 'Vpcs[].{Id:VpcId,CIDR:CidrBlock}' --output table
```

6. Limpiar todo al terminar:

```bash
terraform destroy -auto-approve
docker compose down
```

## Salida esperada

Después de `terraform apply` deberías ver algo similar a:

```
Apply complete! Resources: 10 added, 0 changed, 0 destroyed.

Outputs:

dev_public_subnet_ids = [
  "subnet-xxxxxxxx",
  "subnet-xxxxxxxx",
]
dev_vpc_id = "vpc-xxxxxxxx"
prod_public_subnet_ids = [
  "subnet-xxxxxxxx",
  "subnet-xxxxxxxx",
]
prod_vpc_id = "vpc-xxxxxxxx"
```

Dos VPCs (`dev` y `prod`), cada una con dos subnets públicas y su propio Internet
Gateway, creadas a partir del mismo módulo `modules/vpc-network`.

## Estructura

```
terraform-modules-reutilizacion/
├── docker-compose.yml       # LocalStack (servicio EC2, sin costo, sin cuenta AWS real)
├── main.tf                  # Root module: provider + dos instancias del módulo VPC
└── modules/
    └── vpc-network/
        ├── main.tf           # Recursos: VPC, subnets públicas, Internet Gateway
        ├── variables.tf      # Variables de entrada con validaciones
        └── outputs.tf        # Valores expuestos por el módulo
```

## Notas

- No se usan credenciales reales de AWS: el provider usa `access_key = "test"` /
  `secret_key = "test"`, que es lo que LocalStack espera para autenticación simulada.
- Si preferís probar contra una cuenta AWS real, quitá el bloque `endpoints` del
  provider en `main.tf` y configurá credenciales reales (por ejemplo vía
  `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` o un profile de `~/.aws/credentials`).
  En ese caso vas a incurrir en los costos normales de los recursos AWS creados.
