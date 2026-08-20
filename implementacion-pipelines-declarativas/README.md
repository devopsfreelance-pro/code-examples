# Motor mínimo de pipelines declarativas

Ejemplo de código para el post [Pipelines Declarativas: Guía Completa para Equipos DevOps](https://www.devopsfreelance.pro/blog/posts/implementacion-pipelines-declarativas/).

## Qué demuestra

El post explica declarative pipelines usando Jenkinsfile (Groovy) y `.gitlab-ci.yml`
(YAML) como ejemplos, pero ambos requieren un servidor Jenkins o GitLab CI corriendo
para poder probarlos. Este ejemplo aísla el concepto central del artículo —**separar
la declaración del proceso (qué queremos lograr) de su ejecución (cómo se lleva a
cabo)**— en dos piezas que corren en tu máquina en minutos:

- `pipeline.yml`: la declaración. Un archivo YAML con `stages`, `variables` y jobs
  con `script`, igual en espíritu a un `.gitlab-ci.yml`, incluyendo un job marcado
  `when: manual` como el `deploy` del post.
- `run_pipeline.py`: el motor. Un script Python de ~80 líneas que lee `pipeline.yml`,
  recorre los `stages` en el orden declarado, ejecuta los `script` de cada job,
  sustituye `${VARIABLES}` y respeta `when: manual` (salta el job salvo que se pida
  explícitamente), abortando con el código de salida del comando que falló si algo
  rompe.
- `docker-compose.yml` + `integration_test.sh`: reproducen el ejemplo de "Integración
  con Contenedores y Servicios" del post (`services: postgres, redis` en GitLab CI)
  levantando Postgres y Redis localmente y verificando que la pipeline puede
  conectarse a ellos antes de seguir a `deploy`.

## Requisitos

- Python 3.8+
- `pip install pyyaml`
- Docker y Docker Compose v2 (`docker compose`, no `docker-compose`) para el stage
  `integration_test`

No hace falta cuenta de Jenkins, GitLab ni ningún servicio pago: todo corre local.

## Cómo correrlo

```bash
cd implementacion-pipelines-declarativas

pip install pyyaml

# Corre build, test e integration_test. El job de deploy queda SKIPPED
# porque está marcado `when: manual`, igual que en el .gitlab-ci.yml del post.
python3 run_pipeline.py

# Para incluir también el job de deploy (equivalente a disparar el job manual):
python3 run_pipeline.py --deploy
```

## Salida esperada

```
Pipeline declarada con 4 stages: build, test, integration_test, deploy

=== stage: build / job: build ===
$ echo "Compilando demo-app..."
Compilando demo-app...
$ mkdir -p dist
$ echo "print('hello from demo-app')" > dist/app.py
$ python3 -m py_compile dist/app.py
[OK] job 'build' completado

=== stage: test / job: test ===
$ echo "Ejecutando tests unitarios..."
Ejecutando tests unitarios...
$ python3 -c "assert 1 + 1 == 2, 'math is broken'; print('tests unitarios OK')"
tests unitarios OK
[OK] job 'test' completado

=== stage: integration_test / job: integration_test ===
$ bash integration_test.sh
Levantando servicios (postgres, redis) para pruebas de integracion...
[+] Running 2/2
 ✔ Container ...-postgres-1  Started
 ✔ Container ...-redis-1     Started
[OK] postgres listo en localhost:5432
[OK] redis listo en localhost:6379
Pruebas de integracion simuladas: conectividad con postgres y redis OK
Bajando servicios...
[OK] job 'integration_test' completado

=== stage: deploy / job: deploy === [SKIPPED] (when: manual, usar --deploy)

Pipeline completada con exito.
```

Si algún comando del `script` de un job falla, `run_pipeline.py` imprime `[FAIL]` y
termina con el mismo código de salida que el comando fallido, sin ejecutar los
stages siguientes — el mismo comportamiento "fail fast" que tendría un job real de
Jenkins o GitLab CI.

## Ir más allá

Para acercar esto a Jenkins o GitLab CI reales:

- El `Jenkinsfile` y `.gitlab-ci.yml` del post en `stage('Build')` / `agent { docker
  { image ... } }` equivalen a que cada `script` de este `pipeline.yml` corriera
  dentro de un contenedor Docker en lugar de en el host; se podría extender
  `run_pipeline.py` para envolver cada `script` con `docker run <image> sh -c "..."`.
- `credentials('docker-registry-creds')` del post se resolvería aquí con variables
  de entorno inyectadas desde un gestor de secretos (AWS Secrets Manager, Vault),
  nunca hardcodeadas en `pipeline.yml`.
