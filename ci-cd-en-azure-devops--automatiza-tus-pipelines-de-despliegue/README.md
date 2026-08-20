# CI/CD en Azure DevOps: Automatiza tus Pipelines de Despliegue

Post: https://www.devopsfreelance.pro/blog/posts/ci-cd-en-azure-devops--automatiza-tus-pipelines-de-despliegue/

## Qué demuestra este ejemplo

El post explica cómo armar un pipeline de Azure DevOps con etapas de build,
test, empaquetado y despliegue multi-entorno. Este ejemplo reproduce esas
mismas etapas (Build → Test → Package → Deploy) en miniatura, usando:

- Una app mínima en Python (`app/app.py`) con un endpoint `/health`, sin
  dependencias externas.
- Pruebas unitarias con `pytest` (`app/test_app.py`), equivalente al task
  `DotNetCoreCLI@2 - Run unit tests` del post.
- Un `Dockerfile` que empaqueta la app, equivalente al task `Docker@2 -
  Build and Push`.
- `azure-pipelines.yml`: el pipeline real tal como se vería en Azure
  DevOps, para copiar/adaptar en tu propio proyecto (usa `UsePythonVersion@0`,
  `Docker@2` y un stage `DeployDev` con smoke test, igual que en el artículo).
- `scripts/run_pipeline_locally.sh`: corre localmente con Docker las mismas
  etapas que ejecutaría el pipeline de Azure DevOps (test → build de imagen →
  deploy simulado en un contenedor → smoke test contra `/health`), para que
  puedas ver el flujo funcionando sin necesidad de una cuenta de Azure DevOps.

## Requisitos

- Python 3.9+ con `pip`
- Docker
- `curl`

No hace falta cuenta de Azure ni de Azure DevOps para correr este ejemplo:
`azure-pipelines.yml` queda como referencia de cómo llevarlo a Azure DevOps
una vez que tengas un Service Connection configurado (ver sección siguiente).

## Cómo correrlo

### 1. Solo las pruebas unitarias (equivalente al stage "Build and Test")

```bash
cd ci-cd-en-azure-devops--automatiza-tus-pipelines-de-despliegue
python3 -m pip install --user pytest
python3 -m pytest app/test_app.py -v
```

Salida esperada:

```
app/test_app.py::test_health_payload_status_ok PASSED
app/test_app.py::test_health_payload_service_name PASSED
app/test_app.py::test_health_payload_uses_environment_variable PASSED
app/test_app.py::test_health_payload_defaults_to_development PASSED

4 passed in 0.0Xs
```

### 2. Pipeline completo simulado (Build → Test → Package → Deploy)

```bash
cd ci-cd-en-azure-devops--automatiza-tus-pipelines-de-despliegue
chmod +x scripts/run_pipeline_locally.sh
./scripts/run_pipeline_locally.sh
```

Salida esperada (resumida):

```
==> Stage: Build and Test
--> Running unit tests
4 passed in 0.0Xs
--> Building Docker image (myapp:local)
==> Stage: Deploy to Development (simulado con un contenedor local)
--> Esperando a que el contenedor esté listo
--> Smoke test
{"status": "ok", "service": "myapp", "environment": "development"}
Smoke test PASSED
==> Limpiando contenedor de la demo
Pipeline local completado con éxito.
```

### 3. Probar el contenedor manualmente (opcional)

```bash
docker build -t myapp:local .
docker run -d --name myapp-demo -p 8080:8080 -e APP_ENVIRONMENT=development myapp:local
curl http://localhost:8080/health
## {"status": "ok", "service": "myapp", "environment": "development"}
docker rm -f myapp-demo
```

## Llevarlo a Azure DevOps real

Para ejecutar `azure-pipelines.yml` en un proyecto de Azure DevOps real
necesitás:

- Un proyecto en Azure DevOps con Azure Repos o un repo de GitHub conectado.
- Reemplazar el paso de despliegue (`curl -f https://myapp-dev.azurewebsites.net/health`)
  por tus propios recursos: un App Service, AKS o el destino que uses, y el
  nombre real de tu Service Connection de Azure (`Azure-DevOps-Service-Connection`
  en el post original). Estos valores dependen de tu suscripción de Azure y
  no se incluyen aquí porque son específicos de cada cuenta.
- Crear el pipeline en Azure DevOps apuntando a este `azure-pipelines.yml`.

## Estructura

```
.
├── app/
│   ├── app.py          # App mínima con endpoint /health
│   └── test_app.py     # Pruebas unitarias (pytest)
├── Dockerfile
├── azure-pipelines.yml # Pipeline de referencia para Azure DevOps
├── scripts/
│   └── run_pipeline_locally.sh  # Simula el pipeline completo localmente
└── README.md
```
