# Políticas como código con OPA y Sentinel

Post relacionado: [Políticas como Código: Guía Completa de OPA y Sentinel 2026](https://www.devopsfreelance.pro/blog/posts/politicas-codigo-opa-sentinel/)

## Qué demuestra este ejemplo

El post explica el patrón central de policy-as-code: interceptar un plan de
Terraform y evaluarlo contra políticas versionadas en Rego antes de aplicar
el `apply` (sección "Implementación Práctica en Entornos Empresariales").
Este ejemplo reproduce ese flujo con OPA de forma 100% local, sin necesitar
Terraform instalado ni una cuenta de AWS:

1. `tfplan-sample.json` simula la salida de `terraform show -json` para un
   plan con 4 recursos: dos buckets S3 (uno sin cifrar, uno cifrado) y dos
   instancias EC2 (una con el tipo prohibido `t3.2xlarge`, otra válida). Es
   el mismo escenario que usa el post como ejemplo.
2. `policies/terraform.rego` contiene las dos reglas `deny` del post: bucket
   S3 sin cifrado e instancia con tipo prohibido.
3. `validate.sh` corre `opa eval` vía Docker contra el plan de ejemplo, igual
   que el paso de CI/CD mostrado en el post, y falla (`exit 1`) si hay
   violaciones.
4. `sentinel/mandatory-tags.sentinel` es la política Sentinel del post
   (control de tags obligatorios), incluida como referencia de sintaxis. **No
   es ejecutable localmente**: Sentinel solo corre dentro de Terraform Cloud
   / Terraform Enterprise, no tiene runtime standalone ni imagen Docker
   pública, así que no forma parte de `validate.sh`.

**Nota sobre el post:** el bloque Rego original usa `package
terraform.analysis` pero el script de validación consulta
`data.terraform.deny`, lo cual no coincide (el paquete real sería
`data.terraform.analysis.deny`). En este ejemplo se usa `package terraform`
para que el paquete y la consulta sean consistentes entre sí.

## Requisitos

- Docker (para correr OPA sin instalarlo localmente)
- Nada más: no hace falta Terraform, ni AWS, ni Terraform Cloud

## Cómo correrlo

```bash
cd politicas-codigo-opa-sentinel
./validate.sh
```

El script hace, en orden:

```bash
docker run --rm \
    -v "$(pwd)/policies:/policies" \
    -v "$(pwd)/tfplan-sample.json:/input.json" \
    openpolicyagent/opa:0.68.0 \
    eval --data /policies --input /input.json \
    --format pretty \
    "data.terraform.deny" > violations.json

cat violations.json
```

## Salida esperada

```
Evaluando tfplan-sample.json contra las politicas en policies/ ...
--- Resultado (violations.json) ---
[
  "Bucket S3 'aws_s3_bucket.logs_sin_cifrar' debe tener cifrado habilitado",
  "Instancia 'aws_instance.batch_costoso' usa tipo prohibido t3.2xlarge"
]
Violaciones de politica detectadas. Ver violations.json.
```

El script termina con código de salida `1`, tal como lo haría un pipeline de
CI/CD que bloquea un `terraform apply` cuando el plan viola las políticas
organizacionales. El bucket cifrado y la instancia `t3.medium` no generan
ninguna violación, mostrando que las reglas solo actúan sobre los recursos
no conformes.

Para comprobar el caso "sin violaciones", editá `tfplan-sample.json` y
cambiá `t3.2xlarge` por `t3.medium` y agregá la clave
`server_side_encryption_configuration` al bucket `logs_sin_cifrar`; al
volver a correr `./validate.sh` el resultado será `[]` y el script terminará
con código `0`.
