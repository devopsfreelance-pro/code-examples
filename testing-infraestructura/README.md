# Testing de Infraestructura: pirámide completa en tu máquina

Post: [Testing de Infraestructura para DevOps](https://www.devopsfreelance.pro/blog/posts/testing-infraestructura/)

## Qué demuestra este ejemplo

El post describe una pirámide de cuatro niveles para testear IaC, de más
barato a más caro: **validación estática y lint**, **plan**, **policy as
code sobre el plan**, e **integración real (apply + destroy)**. Este
ejemplo implementa los cuatro niveles contra un módulo Terraform mínimo
(un bucket S3 con cifrado y bloqueo de acceso público), usando
[LocalStack](https://www.localstack.cloud/) como "cuenta de prueba"
gratuita en vez de una cuenta AWS real.

Con esto podés:

1. Correr `terraform validate` y `tflint` sobre el módulo (nivel 1).
2. Generar un `terraform plan` (nivel 2).
3. Evaluar ese plan contra una policy de Open Policy Agent con `conftest`
   que exige que todo bucket S3 tenga cifrado configurado y bloquee ACLs
   públicas (nivel 3) — y ver cómo la policy **bloquea** el plan si se
   desactiva el cifrado.
4. Aplicar la infraestructura de verdad contra LocalStack, verificarla y
   destruirla (nivel 4), tal como describe la sección "Terratest en la
   práctica" del post, pero sin necesidad de Go ni de una cuenta AWS.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/) y Docker Compose (para LocalStack)
- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) (solo para el nivel 4, verificación post-apply)
- Opcional pero recomendado para los niveles 1 y 3:
  - [TFLint](https://github.com/terraform-linters/tflint#installation)
  - [conftest](https://www.conftest.dev/install/)

Si TFLint o conftest no están instalados, el script los omite con un
aviso y sigue con el resto de los niveles.

No se necesita cuenta de AWS ni credenciales reales: LocalStack no las
valida, y el script exporta credenciales dummy (`test`/`test`).

## Estructura

```
testing-infraestructura/
├── docker-compose.yml       # LocalStack (solo servicio S3)
├── terraform/
│   ├── main.tf              # Bucket S3 + cifrado + bloqueo de acceso público
│   └── .tflint.hcl           # Config de TFLint (nivel 1)
├── policy/
│   └── s3.rego               # Policy de conftest (nivel 3)
└── run-pyramid.sh            # Orquesta los 4 niveles
```

## Pasos para correrlo

### 1. Levantar LocalStack

```bash
docker compose up -d
```

Esperá a que el healthcheck pase (unos segundos):

```bash
docker inspect --format='{{.State.Health.Status}}' testing-infra-localstack
```

Debe mostrar `healthy`.

### 2. Correr los niveles 1 a 3 (validate, lint, plan + policy)

```bash
./run-pyramid.sh
```

Salida esperada (resumida):

```
== Nivel 1: validación estática y linting ==
Success! The configuration is valid.

== Nivel 2: plan ==
...
Plan: 3 to add, 0 to change, 0 to destroy.

== Nivel 3: policy as code sobre el plan ==
2 tests, 2 passed, 0 warnings, 0 failures, 0 exceptions
```

### 3. Ver a la policy bloquear un plan inseguro

```bash
./run-pyramid.sh --break
```

Esto fuerza `enable_encryption=false` y la policy debe fallar el plan:

```
FAIL - - main - Hay al menos un aws_s3_bucket en el plan sin
aws_s3_bucket_server_side_encryption_configuration asociado

2 tests, 1 passed, 0 warnings, 1 failure, 0 exceptions
```

El script termina con código de salida distinto de cero en este caso
(así es como se engancharía en un pipeline real).

### 4. Correr también el nivel 4 (integración real contra LocalStack)

```bash
./run-pyramid.sh --apply
```

Esto aplica el bucket contra LocalStack, verifica con `aws s3api
head-bucket` que existe, y lo destruye automáticamente al finalizar
(incluso si algo falla en el medio, gracias al `trap` sobre `destroy`,
el mismo patrón que `defer terraform.Destroy(t, opts)` en Terratest).

Salida esperada (resumida):

```
== Nivel 4: integración real contra LocalStack (apply + destroy) ==
aws_s3_bucket.demo: Creation complete after 1s [id=testing-infra-demo-bucket]
...
Verificando que el bucket existe en LocalStack...
OK: bucket 'testing-infra-demo-bucket' confirmado en LocalStack. Destruyendo...
...
Destroy complete! Resources: 3 destroyed.
```

### 5. Apagar LocalStack

```bash
docker compose down -v
```

## Notas

- `main.tf` apunta el provider de AWS al endpoint de LocalStack
  (`http://localhost:4566`) con `skip_credentials_validation` y
  `s3_use_path_style`, el patrón estándar para testear contra
  LocalStack sin tocar una cuenta real.
- `policy/s3.rego` está simplificada a propósito para un solo bucket de
  demo: en un repo real, cada regla recorrería todos los `aws_s3_bucket`
  del plan y los matchearía contra su configuración específica por
  dirección del módulo, no por nombre fijo.
- Si instalás el plugin `aws` de TFLint (declarado en `.tflint.hcl`),
  la primera corrida necesita internet para descargarlo con
  `tflint --init` dentro de `terraform/`.
