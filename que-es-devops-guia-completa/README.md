# Qué es DevOps: mini pipeline Code → Build → Test → Deploy

Post: [Qué es DevOps: Guía Completa de Cultura, Herramientas y Carrera](https://www.devopsfreelance.pro/blog/posts/que-es-devops-guia-completa/)

## Qué demuestra

El post explica el ciclo de vida DevOps (`Plan → Code → Build → Test → Release →
Deploy → Operate → Monitor`) y usa como ejemplo un pipeline de CI/CD con GitHub
Actions. Este directorio contiene una versión mínima pero real de ese ciclo,
ejecutable en tu máquina en minutos:

- **Code**: `app.py`, un servicio HTTP mínimo (solo librería estándar de Python,
  sin dependencias externas) con endpoints `/` y `/health`.
- **Test**: `test_app.py`, tests unitarios sobre la lógica de negocio.
- **Build**: `Dockerfile`, empaqueta la app en una imagen inmutable.
- **Deploy/Operate**: `docker-compose.yml`, levanta el contenedor y expone el
  puerto 8080 con healthcheck.
- **Automatización (CI)**: `.github/workflows/ci.yml`, reproduce las mismas
  fases (test, build, smoke test) como pipeline de CI, igual al ejemplo de
  GitHub Actions del post.

No hay ningún placeholder ni cuenta cloud involucrada: todo corre localmente
con Docker.

## Requisitos

- Python 3.9+ (para correr los tests sin contenedor)
- Docker y Docker Compose (`docker compose version`)

## Pasos para correrlo

### 1. Fase Test: correr los tests unitarios directamente

```bash
cd que-es-devops-guia-completa
python3 -m unittest test_app.py -v
```

Salida esperada (resumen):

```
test_includes_message (test_app.TestRootPayload) ... ok
test_includes_version (test_app.TestRootPayload) ... ok
test_includes_version (test_app.TestHealthPayload) ... ok
test_status_is_ok (test_app.TestHealthPayload) ... ok

Ran 4 tests in 0.00Xs

OK
```

### 2. Fase Build + Deploy: levantar el servicio con Docker Compose

```bash
docker compose up --build -d
```

Verificar que el contenedor esté sano:

```bash
docker compose ps
```

Salida esperada: el servicio `app` en estado `running (healthy)`.

### 3. Probar los endpoints (fase Operate/Monitor)

```bash
curl http://localhost:8080/
curl http://localhost:8080/health
```

Salida esperada:

```json
{"message": "Hola DevOps", "version": "1.0.0"}
{"status": "ok", "version": "1.0.0"}
```

### 4. Apagar el entorno

```bash
docker compose down
```

## Automatización con CI

`.github/workflows/ci.yml` reproduce el mismo flujo (test → build → smoke test)
como pipeline de GitHub Actions. Si subís este directorio a un repo propio en
GitHub, el workflow corre automáticamente en cada push/PR a `main` sin
necesidad de configurar secretos ni cuentas cloud.
