# Python DevOps: automatización de infraestructura con boto3

Ejemplo de código para el post del blog:
[Python DevOps: Automatización Profesional en 2026](https://www.devopsfreelance.pro/blog/posts/python-automatizacion-devops/)

## Qué demuestra

El post explica cómo Python (con boto3) se usa para gestionar infraestructura
cloud como código, aplicando patrones robustos de automatización: reintentos
con backoff exponencial, tagging de recursos y logging estructurado.

Este ejemplo implementa esos mismos patrones contra un bucket S3 real (aunque
simulado localmente con LocalStack, así no requiere cuenta de AWS ni genera
costos):

- `automate_infra.py` crea un bucket S3, le aplica tags, sube un objeto y
  verifica el resultado, todo con un decorador `retry_with_backoff` que
  reintenta automáticamente ante fallos transitorios de la API.
- `docker-compose.yml` levanta LocalStack, que expone una API compatible con
  S3 en `localhost:4566`.

## Requisitos

- Docker y Docker Compose
- Python 3.10+ con `pip`

## Pasos para correrlo

1. Levantar LocalStack:

   ```bash
   docker compose up -d
   ```

2. Esperar a que el healthcheck esté OK (unos segundos):

   ```bash
   docker compose ps
   ```

3. Crear un entorno virtual e instalar dependencias:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. Ejecutar el script de automatización:

   ```bash
   python automate_infra.py
   ```

5. Al terminar, apagar LocalStack:

   ```bash
   docker compose down
   ```

## Salida esperada

```
2026-08-20 12:00:00,000 [INFO] Iniciando automatización de infraestructura (LocalStack: http://localhost:4566)
2026-08-20 12:00:00,050 [INFO] Bucket 'devops-automation-demo' creado
2026-08-20 12:00:00,090 [INFO] Tags aplicados a 'devops-automation-demo'
2026-08-20 12:00:00,120 [INFO] Objeto 'reports/status.txt' subido a 'devops-automation-demo'
2026-08-20 12:00:00,150 [INFO] Verificación final:
2026-08-20 12:00:00,150 [INFO]   Bucket: devops-automation-demo
2026-08-20 12:00:00,150 [INFO]   Tags: {'Environment': 'demo', 'ManagedBy': 'python-automation', 'Project': 'devopsfreelance-blog'}
2026-08-20 12:00:00,150 [INFO]   Contenido de 'reports/status.txt': 'Automatización ejecutada correctamente.'
2026-08-20 12:00:00,151 [INFO] Automatización completada con éxito.
```

Si se corre el script una segunda vez, el log mostrará
`Bucket 'devops-automation-demo' ya existe, se reutiliza` en vez de crearlo
de nuevo, ilustrando el patrón idempotente que se espera de scripts de
infraestructura como código.

## Notas

- Las credenciales `test`/`test` en `automate_infra.py` son las que exige
  LocalStack por convención; no son secretos reales y no aplican fuera de
  este entorno local.
- Para usarlo contra AWS real, basta con quitar `endpoint_url` en
  `get_s3_client()` y dejar que boto3 resuelva credenciales vía variables de
  entorno, perfil compartido (`~/.aws/credentials`) o rol IAM, tal como
  describe el post en la sección de seguridad de credenciales.
