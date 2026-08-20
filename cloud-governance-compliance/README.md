# Cloud governance y compliance: policy-as-code con Terraform + OPA/Conftest

Post relacionado: [Guía Completa de Cloud governance y compliance](https://www.devopsfreelance.pro/blog/posts/cloud-governance-compliance/)

## Qué demuestra este ejemplo

El post explica que las políticas de governance efectivas no deberían depender
de revisión manual ni de documentos: deben ser código versionado y ejecutable
(sección "Policy-as-Code: OPA y Sentinel"). Este ejemplo reproduce ese flujo
completo con herramientas reales, sin necesitar una cuenta de AWS:

1. `terraform/main.tf` define cuatro recursos: dos buckets S3 (uno cifrado,
   uno sin cifrar) y dos instancias EC2 (una con el tag `Environment`
   obligatorio, otra sin él) — el mismo escenario de incumplimiento que usa
   el post como ejemplo.
2. `terraform plan` genera un plan sin tocar AWS de verdad (se usan
   credenciales dummy, `terraform plan` no requiere una cuenta válida para
   crear recursos nuevos).
3. `policy/terraform.rego` es la misma política Rego del post: deniega
   buckets S3 sin cifrado y adds recursos EC2 sin el tag `Environment`.
4. Conftest evalúa el plan JSON contra esa política, igual que en un pipeline
   de CI antes de un `terraform apply`.

El resultado esperado es que Conftest **falle** (exit code 1) señalando
exactamente los dos recursos no conformes, demostrando cómo un guardrail de
policy-as-code detiene un despliegue inseguro antes de que llegue a
producción.

## Requisitos

- [Terraform](https://developer.hashicorp.com/terraform/install) (probado con 1.15)
- Docker (para correr Conftest sin instalarlo localmente)
- No hace falta cuenta de AWS: se usan credenciales dummy solo para que el
  provider pueda generar el plan.

## Cómo correrlo

```bash
cd cloud-governance-compliance
./run.sh
```

El script hace, en orden:

```bash
cd terraform
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="us-east-1"

terraform init -input=false
terraform plan -input=false -out=tfplan
terraform show -json tfplan > tfplan.json

cd ..
docker run --rm -v "$(pwd)":/project -w /project \
  openpolicyagent/conftest test terraform/tfplan.json --policy policy --all-namespaces
```

## Salida esperada

```
== conftest test (OPA policy-as-code) ==
FAIL - terraform/tfplan.json - terraform.aws - Instance 'noncompliant' is missing required 'Environment' tag
FAIL - terraform/tfplan.json - terraform.aws - S3 bucket 'noncompliant' must have encryption enabled

2 tests, 0 passed, 0 warnings, 2 failures, 0 exceptions
```

El script termina con código de salida distinto de cero porque Conftest
encontró violaciones, tal como haría en un pipeline de CI/CD real (el paso de
policy-as-code bloquearía el `terraform apply`). Si corregís `main.tf`
agregando cifrado al bucket `noncompliant` y el tag `Environment` a la
instancia `noncompliant`, `conftest test` pasa con `0 failures`.

## Notas

- `terraform/.terraform/`, `tfplan` y `tfplan.json` quedan excluidos por
  `.gitignore`: son artefactos locales de cada corrida.
- El provider AWS se fija en `~> 3.75` porque en esa serie `aws_s3_bucket`
  todavía admite el bloque `server_side_encryption_configuration` inline,
  igual que en la política Rego del post. En provider 4+ ese bloque se movió
  a un recurso separado (`aws_s3_bucket_server_side_encryption_configuration`)
  y la política tendría que ajustarse.
