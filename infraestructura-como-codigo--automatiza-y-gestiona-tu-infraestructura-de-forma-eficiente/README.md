# Infraestructura como Código: ejemplo mínimo con Terraform + LocalStack

Post: [Infraestructura como Código: Automatiza y Gestiona tu Infraestructura de Forma Eficiente](https://www.devopsfreelance.pro/blog/posts/infraestructura-como-codigo--automatiza-y-gestiona-tu-infraestructura-de-forma-eficiente/)

## Qué demuestra

Una versión mínima y ejecutable del ejemplo de Terraform del post: define de forma
**declarativa** (no imperativa) una VPC con subred pública y un bucket S3, todo con
tags gestionados centralmente (`default_tags`), variables con validación, y outputs.

Corre contra [LocalStack](https://www.localstack.cloud/) (simulador de AWS en un
contenedor Docker), así que no necesitás cuenta de AWS ni vas a generar costos.
Podés ejecutar `terraform apply` las veces que quieras: al ser idempotente, el
segundo `apply` no crea recursos duplicados, solo confirma que el estado ya coincide
con lo declarado (el principio central de IaC que explica el post).

## Requisitos

- Docker y Docker Compose
- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5
- `curl` (para el healthcheck de LocalStack)

## Pasos

1. Levantar LocalStack:

   ```bash
   docker compose up -d
   ```

2. Esperar a que esté sano (unos segundos):

   ```bash
   until curl -s http://localhost:4566/_localstack/health | grep -q '"s3": "available"'; do sleep 2; done
   ```

3. Inicializar y aplicar Terraform:

   ```bash
   terraform init
   terraform plan
   terraform apply -auto-approve
   ```

4. Ver los outputs:

   ```bash
   terraform output
   ```

5. Confirmar idempotencia (no debería reportar cambios):

   ```bash
   terraform plan
   ```

6. Limpiar todo:

   ```bash
   terraform destroy -auto-approve
   docker compose down -v
   ```

## Salida esperada

Tras el `apply`, Terraform reporta algo como:

```
Apply complete! Resources: 6 added, 0 changed, 0 destroyed.

Outputs:

artifacts_bucket = "iac-demo-artifacts-development"
public_subnet_id = "subnet-xxxxxxxxxxxxxxxxx"
vpc_id = "vpc-xxxxxxxxxxxxxxxxx"
```

Y el segundo `terraform plan` (paso 5) debe mostrar:

```
No changes. Your infrastructure matches the configuration.
```

## Notas

- Las credenciales `test`/`test` en `main.tf` son las que exige el proveedor AWS
  de Terraform para apuntar a LocalStack; no son secretos reales, no funcionan
  contra AWS de verdad.
- Este ejemplo cubre el núcleo del post (declarativo, idempotente, tags, variables,
  outputs). El post también cubre CDK, Pulumi, pipelines de CI/CD, políticas OPA y
  testing con Terratest, que quedan fuera de este mini-ejemplo por alcance.
