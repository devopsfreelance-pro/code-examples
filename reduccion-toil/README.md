# Reduccion de Toil: medicion y auto-remediacion

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
