# Infrastructure from Code (IfC) - mini motor de ejemplo

Post del blog: [Infrastructure from Code: Guía completa para DevOps 2026](https://www.devopsfreelance.pro/blog/posts/infrastructure-from-code-ifc/)

## Qué demuestra este ejemplo

El post explica que frameworks como Nitric, Klotho o Ampt analizan el código de una aplicación (sin ejecutarlo), detectan qué recursos cloud usa (buckets, colas, APIs) y generan automáticamente la infraestructura necesaria, en vez de que el desarrollador escriba Terraform o CloudFormation a mano.

Este ejemplo implementa una versión mínima y didáctica de ese mismo mecanismo, en Python puro:

- `ifc_sdk.py`: un SDK de juguete (`bucket()`, `queue()`, `api()`, `.allow()`) parecido en espíritu al SDK de Nitric usado en el post, solo para declarar recursos en el código de aplicación.
- `app.py`: el "código de aplicación", equivalente en Python al ejemplo TypeScript/Nitric del post (una API que sube una imagen a un bucket y encola un job de resize).
- `ifc_analyzer.py`: el "framework de IfC". Usa el módulo `ast` de Python para analizar `app.py` de forma **estática** (sin importarlo ni ejecutarlo), detecta las llamadas a `bucket()`, `queue()` y `api()` con sus permisos `.allow(...)`, y genera automáticamente un archivo Terraform (`generated_infra.tf`) con los recursos AWS equivalentes (S3, SQS, API Gateway v2).

No es el framework Nitric real (que requiere su propio CLI, Docker y una cuenta cloud para desplegar). Es una implementación propia y simplificada del principio de "generar infraestructura a partir del análisis del código", pensada para poder ejecutarse en minutos sin instalar nada más que Python.

## Requisitos

- Python 3.8 o superior (sin dependencias externas, solo librería estándar)
- Opcional: Terraform CLI, si querés validar el `.tf` generado (`terraform validate`)

## Cómo correrlo

```bash
cd infrastructure-from-code-ifc
python3 ifc_analyzer.py app.py
```

### Salida esperada

```
Analisis estatico de app.py:
RECURSO                        TIPO       PERMISOS
image-processor                api        -
uploaded-images                bucket     read, write
resize-jobs                    queue      send, receive

3 recursos detectados.
Infraestructura generada en: generated_infra.tf
```

Esto crea `generated_infra.tf` con los tres recursos de AWS (API Gateway, S3, SQS) deducidos automáticamente a partir de las declaraciones en `app.py`, sin que nadie haya escrito una línea de HCL.

### Validar el Terraform generado (opcional)

```bash
mkdir -p /tmp/ifc-validate && cp generated_infra.tf /tmp/ifc-validate/main.tf
cd /tmp/ifc-validate
terraform init -backend=false
terraform validate
```

Salida esperada: `Success! The configuration is valid.`

### Para ver el mecanismo "cambia el código, cambia la infra"

Agregá un recurso nuevo en `app.py` (por ejemplo `notifications = queue("notifications")`) y volvé a correr `python3 ifc_analyzer.py app.py`. El nuevo recurso aparece automáticamente en `generated_infra.tf`, sin tocar Terraform a mano, que es exactamente la idea central de Infrastructure from Code descripta en el post.
