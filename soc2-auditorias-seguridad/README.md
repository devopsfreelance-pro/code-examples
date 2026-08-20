# SOC2: automatizando un control de seguridad como evidencia de auditoría

Post: [SOC2 Compliance: Guía Completa para Auditorías 2026](https://www.devopsfreelance.pro/blog/posts/soc2-auditorias-seguridad/)

## Qué demuestra este ejemplo

El post explica que la diferencia entre un programa SOC2 sostenible y uno agotador
está en la automatización: en lugar de revisar manualmente si cada bucket S3 nuevo
cumple los controles de seguridad, se define el control **una sola vez como código**
(policy as code con [Open Policy Agent](https://www.openpolicyagent.org/)) y se evalúa
automáticamente contra el plan de Terraform en cada cambio de infraestructura, tal
como hace la startup SaaS del caso de uso del artículo (Terraform + OPA + gate en
el pipeline de CI/CD).

Este ejemplo implementa un control típico del criterio **Seguridad / Confidencialidad
(CC6.1)** de los Trust Services Criteria de SOC2: *todo bucket S3 nuevo debe tener
cifrado server-side, bloqueo de acceso público y versionado habilitados*.

Incluye:

- `main.tf`: dos buckets S3. `compliant` cumple los tres controles; `noncompliant`
  no cumple ninguno (simula un cambio que un desarrollador sube sin revisar los
  controles).
- `policy/soc2_controls.rego`: la política OPA que codifica el control CC6.1 y
  evalúa el plan de Terraform en formato JSON.
- `generate-evidence.sh`: script que corre `terraform plan`, lo evalúa con OPA y
  genera un archivo `evidence-<timestamp>.json` con el resultado, tal como lo
  haría un job de CI/CD antes de cada despliegue o una herramienta de audit
  automation (Vanta, Drata, etc.) al recolectar evidencia continua para un
  informe SOC2 Tipo II.

El script termina con código de salida distinto de cero si algún bucket no
cumple el control, para poder usarse como gate en un pipeline.

## Requisitos

- [Terraform](https://developer.hashicorp.com/terraform/downloads) >= 1.5
- [Docker](https://docs.docker.com/get-docker/) (para correr OPA sin instalarlo,
  el script lo usa automáticamente si no encuentra el binario `opa` en el PATH)
- Opcional: [OPA CLI](https://www.openpolicyagent.org/docs/latest/#running-opa)
  instalado localmente, si preferís no usar Docker
- Python 3 (ya viene en casi cualquier distro; se usa solo para parsear el JSON
  de salida de OPA)
- Acceso a internet para descargar el provider de AWS y (la primera vez) la
  imagen `openpolicyagent/opa`

No hace falta una cuenta de AWS real: el provider está configurado con
`skip_credentials_validation` y credenciales falsas (`test`/`test`), porque
`terraform plan` sobre recursos que todavía no existen no necesita llamar a la
API de AWS.

## Cómo correrlo

```bash
cd soc2-auditorias-seguridad
./generate-evidence.sh
```

El script hace, en orden:

1. `terraform init` (descarga el provider de AWS)
2. `terraform plan -out=tfplan` (calcula la creación de los dos buckets)
3. `terraform show -json tfplan > tfplan.json` (convierte el plan a JSON)
4. Evalúa `tfplan.json` contra `policy/soc2_controls.rego` con `opa eval`
5. Escribe `evidence-<timestamp>.json` con el veredicto y sale con código 1 si
   hay incumplimientos

## Salida esperada

El script debería terminar con `status: FAIL`, porque `noncompliant` no cumple
ninguno de los tres controles, y el archivo de evidencia generado debería verse
así (timestamp variará):

```json
{
  "control": "CC6.1 - Logical Access / Confidentiality (cifrado, acceso publico y versionado en buckets S3)",
  "timestamp": "2026-08-20T15:06:08Z",
  "status": "FAIL",
  "tool": "opa eval sobre terraform plan (policy as code)",
  "findings": [
    "SOC2 CC6.1: el bucket 'soc2-demo-noncompliant-bucket' no bloquea el acceso publico (aws_s3_bucket_public_access_block con las 4 flags en true)",
    "SOC2 CC6.1: el bucket 'soc2-demo-noncompliant-bucket' no tiene cifrado server-side configurado (aws_s3_bucket_server_side_encryption_configuration)",
    "SOC2 CC6.1: el bucket 'soc2-demo-noncompliant-bucket' no tiene versionado habilitado (aws_s3_bucket_versioning)"
  ]
}
```

El proceso termina con `exit 1` (así es como este mismo script cortaría un
pipeline de CI/CD antes de aplicar un cambio que rompe un control SOC2).

Para comprobar que el bucket `compliant` sí pasa el control, podés comentar o
borrar el bloque `resource "aws_s3_bucket" "noncompliant"` (y sus dependientes,
si los tuviera) en `main.tf` y volver a correr `./generate-evidence.sh`: el
resultado debería ser `status: PASS`, `findings: []` y código de salida 0.

## Limpieza

El script genera `.terraform/`, `tfplan`, `tfplan.json`,
`.terraform.lock.hcl` y `evidence-*.json` localmente (no se aplica nada en AWS,
es solo `terraform plan`). Para borrarlos:

```bash
rm -rf .terraform tfplan tfplan.json .terraform.lock.hcl evidence-*.json
```
