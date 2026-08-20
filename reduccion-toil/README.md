# Reducing Toil: Measurement and Auto-Remediation

Post: [Reduce Toil in SRE: Automation Strategies for DevOps Teams](https://www.devopsfreelance.pro/blog/en/posts/reduce-toil-sre-devops/)

## What this example demonstrates

Two of the core strategies from the post, in runnable code:

1. **Toil measurement** (`analizar_toil.py`): given a CSV of tickets
   classified by category (`toil`, `ingenieria`, `ops_complejo`), it
   calculates what percentage of the team's time goes into repetitive
   manual work and alerts if it exceeds the 50% threshold recommended by
   Google SRE.

2. **Auto-remediation** (`watcher.sh` + `flaky_app.py`): an HTTP service
   (`flaky-service`) simulates progressive degradation (it starts failing
   its healthcheck after ~25 seconds of uptime, with increasing
   probability). A `watcher` container monitors `/health` every 5 seconds
   and, if it detects 3 consecutive failures, runs `docker restart` on the
   service with no human intervention. This is exactly the "manually
   restart the service every time it fails" pattern turned from pure toil
   into automation.

## Requirements

- Docker and Docker Compose (`docker compose version`)
- Python 3.10+ with `pandas` to run the toil analysis locally
  (optional: can also be run inside a venv)

## Steps to run it

### 1. Auto-remediation (Docker Compose)

```bash
cd reduccion-toil
docker compose up --build
```

You'll see in the logs:

- `flaky-service` responding OK for the first ~25 seconds.
- After that, `watcher` reports growing failures on `/health`.
- On the third consecutive failure, `watcher` prints `Reiniciando
  reduccion-toil-flaky (auto-remediacion)...` and runs `docker restart`.
- `flaky-service` starts responding OK again (the restart resets its
  internal uptime), without anyone touching the keyboard.

To check the service status at any time, in another terminal:

```bash
curl http://localhost:8080/health
```

To stop the demo:

```bash
docker compose down
```

### 2. Toil measurement (standalone script)

```bash
cd reduccion-toil
pip install pandas
python3 analizar_toil.py tickets_ejemplo.csv
```

Expected output:

```
ALERTA: Toil representa 50.6% del tiempo (limite recomendado: 50%)
Recomendacion: priorizar iniciativas de automatizacion

Distribucion de Trabajo:
              horas_invertidas  cantidad_tickets  porcentaje_tiempo
categoria
ingenieria                  29                 5          34.117647
ops_complejo                13                 3          15.294118
toil                         43                12          50.588235
```

The point of the example: with `tickets_ejemplo.csv` the team is above
50% toil, which per the post means innovation capacity is compromised and
automation needs to be prioritized (like the `watcher.sh` in this same
directory).

## Files

- `flaky_app.py` / `Dockerfile.flaky` - HTTP service that simulates
  progressive health degradation.
- `watcher.sh` / `Dockerfile.watcher` - watcher that detects health
  failures and runs `docker restart` automatically (requires access to
  the Docker socket, mounted as a volume in `docker-compose.yml`).
- `docker-compose.yml` - orchestrates both containers on the same network.
- `analizar_toil.py` / `tickets_ejemplo.csv` - script and sample data to
  measure the team's time distribution between toil and engineering.

## Notes

- The `watcher` needs access to the host's Docker socket
  (`/var/run/docker.sock`) to be able to restart the monitored service's
  container. In a real environment this is replaced by the Kubernetes API
  (liveness/readiness probes) or whichever orchestrator you use; here
  Docker is used directly to keep the example minimal and free of
  external dependencies.
- There are no secrets or credentials in this example.

---

## 🇪🇸 Versión en español

Post: [Reducir Toil: Estrategias Efectivas para Equipos DevOps](https://www.devopsfreelance.pro/blog/posts/reduccion-toil/)

## Que demuestra este ejemplo

Dos de las estrategias centrales del post, en codigo ejecutable:

1. **Medicion de toil** (`analizar_toil.py`): a partir de un CSV de tickets
   clasificados por categoria (`toil`, `ingenieria`, `ops_complejo`), calcula
   que porcentaje del tiempo del equipo se va en trabajo manual repetitivo y
   alerta si supera el 50% recomendado por Google SRE.

2. **Auto-remediacion** (`watcher.sh` + `flaky_app.py`): un servicio HTTP
   (`flaky-service`) simula degradacion progresiva (empieza a fallar su
   healthcheck despues de ~25 segundos de uptime, cada vez con mas
   probabilidad). Un contenedor `watcher` monitorea `/health` cada 5
   segundos y, si detecta 3 fallos consecutivos, ejecuta
   `docker restart` sobre el servicio sin intervencion humana. Esto es
   exactamente el patron "reiniciar manualmente el servicio cada vez que
   falla" convertido de toil puro en automatizacion.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- Python 3.10+ con `pandas` para correr el analisis de toil localmente
  (opcional: tambien se puede correr dentro de un venv)

## Pasos para correrlo

### 1. Auto-remediacion (Docker Compose)

```bash
cd reduccion-toil
docker compose up --build
```

Vas a ver en los logs:

- `flaky-service` respondiendo OK los primeros ~25 segundos.
- Despues, `watcher` reporta fallos crecientes en `/health`.
- Al tercer fallo consecutivo, `watcher` imprime `Reiniciando
  reduccion-toil-flaky (auto-remediacion)...` y ejecuta `docker restart`.
- `flaky-service` vuelve a responder OK (el reinicio resetea su uptime
  interno), sin que nadie haya tocado el teclado.

Para confirmar el estado del servicio en cualquier momento, en otra
terminal:

```bash
curl http://localhost:8080/health
```

Para cortar la demo:

```bash
docker compose down
```

### 2. Medicion de toil (script standalone)

```bash
cd reduccion-toil
pip install pandas
python3 analizar_toil.py tickets_ejemplo.csv
```

Salida esperada:

```
ALERTA: Toil representa 50.6% del tiempo (limite recomendado: 50%)
Recomendacion: priorizar iniciativas de automatizacion

Distribucion de Trabajo:
              horas_invertidas  cantidad_tickets  porcentaje_tiempo
categoria
ingenieria                  29                 5          34.117647
ops_complejo                13                 3          15.294118
toil                         43                12          50.588235
```

El punto del ejemplo: con `tickets_ejemplo.csv` el equipo esta por encima
del 50% de toil, lo que segun el post significa que la capacidad de
innovacion esta comprometida y hay que priorizar automatizacion (como el
`watcher.sh` de este mismo directorio).

## Archivos

- `flaky_app.py` / `Dockerfile.flaky` - servicio HTTP que simula
  degradacion progresiva de salud.
- `watcher.sh` / `Dockerfile.watcher` - watcher que detecta fallos de
  salud y ejecuta `docker restart` automaticamente (requiere acceso al
  socket de Docker, montado como volumen en `docker-compose.yml`).
- `docker-compose.yml` - orquesta ambos contenedores en la misma red.
- `analizar_toil.py` / `tickets_ejemplo.csv` - script y datos de ejemplo
  para medir la distribucion de tiempo del equipo entre toil e ingenieria.

## Notas

- El `watcher` necesita acceso al socket de Docker del host
  (`/var/run/docker.sock`) para poder reiniciar el contenedor del
  servicio monitoreado. En un entorno real esto se reemplaza por la API
  de Kubernetes (liveness/readiness probes) o del orquestador que uses;
  aca se usa Docker directo para mantener el ejemplo mínimo y sin
  dependencias externas.
- No hay secretos ni credenciales en este ejemplo.
