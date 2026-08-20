# CI/CD con GitHub Actions

Post: https://www.devopsfreelance.pro/blog/posts/ci-cd-con-github-actions/

## Qué demuestra este ejemplo

El post muestra un workflow de GitHub Actions con dos jobs encadenados
(`build-and-test` y `deploy`, con `needs:`) que instala dependencias, corre
tests y despliega. Este ejemplo reproduce ese mismo pipeline en miniatura:

- Una app mínima en Node.js (`app/index.js`) con un endpoint `/health`, sin
  dependencias externas (usa solo el módulo `http` de Node).
- Tests con el test runner nativo de Node (`app/index.test.js`, `node --test`),
  equivalente al `npm test` del workflow del post.
- Un `Dockerfile` que empaqueta la app.
- `.github/workflows/ci.yml`: el workflow real de GitHub Actions, con el
  mismo patrón `build-and-test` → `deploy` (`needs: build-and-test`) del
  post, listo para correr en GitHub apenas hagas push a un repo propio.
- `scripts/run_pipeline_locally.sh`: reproduce localmente con Docker las
  mismas etapas que ejecutaría el workflow (test → build de imagen → deploy
  simulado en un contenedor → smoke test contra `/health`), para ver el
  flujo funcionando sin necesidad de pushear a GitHub.

## Requisitos

- Node.js 20+ (para correr los tests directamente)
- Docker
- `curl`

No hace falta cuenta de GitHub para probar el ejemplo localmente. El archivo
`.github/workflows/ci.yml` queda como referencia de cómo se vería el mismo
pipeline corriendo en GitHub Actions una vez que subas este código a un
repositorio propio.

## Cómo correrlo

### 1. Solo los tests (equivalente al step "Run tests" del job build-and-test)

```bash
cd ci-cd-con-github-actions/app
npm test
```

Salida esperada:

```
# tests 4
# suites 0
# pass 4
# fail 0
# cancelled 0
# skipped 0
```

### 2. Pipeline completo simulado (build-and-test → deploy)

```bash
cd ci-cd-con-github-actions
chmod +x scripts/run_pipeline_locally.sh
./scripts/run_pipeline_locally.sh
```

Salida esperada (resumida):

```
==> Job: build-and-test
--> Corriendo tests (node --test)
# pass 4
--> Construyendo imagen Docker (ci-cd-github-actions-demo:local)
==> Job: deploy (simulado con un contenedor local)
--> Esperando a que el contenedor esté listo
--> Smoke test
{"status":"ok","service":"ci-cd-github-actions-demo","environment":"production"}
Smoke test PASSED
Pipeline local completado con éxito.
==> Limpiando contenedor de la demo
```

### 3. Probar el contenedor manualmente (opcional)

```bash
cd ci-cd-con-github-actions
docker build -t ci-cd-github-actions-demo:local .
docker run -d --name demo -p 8080:8080 -e APP_ENVIRONMENT=production ci-cd-github-actions-demo:local
curl http://localhost:8080/health
## {"status":"ok","service":"ci-cd-github-actions-demo","environment":"production"}
docker rm -f demo
```

## Llevarlo a GitHub Actions real

Para que `.github/workflows/ci.yml` corra en GitHub tal cual está:

1. Copiá esta carpeta (`ci-cd-con-github-actions/`, incluida `.github/`) a la
   raíz de un repositorio propio en GitHub, o ajustá los `working-directory`
   del workflow si la dejás anidada.
2. Hacé push a la rama `main`: el job `build-and-test` corre tests y build de
   imagen en cada push/PR; el job `deploy` corre solo en `main` y hace un
   deploy simulado (mismo contenedor local que usa el script) con smoke test.
3. No requiere secrets ni credenciales de ningún proveedor cloud: el
   "deploy" es un contenedor Docker efímero dentro del propio runner de
   GitHub, pensado para mostrar el flujo `needs:` y el gate de tests antes
   de desplegar. Para un deploy real (a AWS, Azure, un registry, etc.)
   reemplazá el step "Deploy" por tus propios comandos y agregá las
   credenciales correspondientes como GitHub Secrets (`Settings > Secrets
   and variables > Actions`), tal como explica el post.

## Estructura

```
.
├── .github/
│   └── workflows/
│       └── ci.yml       # Workflow real de GitHub Actions (build-and-test -> deploy)
├── app/
│   ├── index.js         # App mínima con endpoint /health
│   ├── index.test.js    # Tests (node --test)
│   └── package.json
├── Dockerfile
├── scripts/
│   └── run_pipeline_locally.sh  # Simula el pipeline completo localmente
└── README.md
```
