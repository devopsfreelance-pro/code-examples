# Automatización de nodos blockchain: health checks + auto-pruning

Ejemplo ejecutable que acompaña al post [Guía Completa de Automatización de nodos blockchain](https://www.devopsfreelance.pro/blog/posts/automatizacion-nodos-blockchain/).

## Qué demuestra

El post cubre IaC (Terraform/Ansible), pipelines de actualización, pruning automatizado, backups y health checks para nodos Ethereum. Levantar un nodo Ethereum real requiere horas de sincronización y GBs de disco, así que este ejemplo aterriza los dos scripts más reutilizables del post contra **mocks HTTP** de un cliente de ejecución (tipo geth) y un cliente de consenso (tipo lighthouse):

1. **`health-check.sh`** (adaptado del post): consulta `eth_syncing` / `net_peerCount` por JSON-RPC y `/eth/v1/node/health` / `/eth/v1/node/syncing` por REST, igual que en producción, y devuelve `exit 1` si el nodo no cumple el mínimo de peers o el beacon no está sano.
2. **`auto-prune-demo.sh`** (adaptado de `scripts/auto-prune.sh` del post): en vez de leer `df` sobre un disco real, mide el tamaño de un directorio de datos simulado contra un límite en MB. La lógica de decisión (umbral superado → parar servicio → podar los archivos más viejos → reiniciar servicio) es exactamente la misma que usarías con `geth snapshot prune-state` en un nodo real.

Con Docker Compose se levantan 4 mocks (`execution-healthy`, `consensus-healthy`, `execution-degraded`, `consensus-degraded`) y un contenedor `monitor` que corre ambos scripts contra el par sano y el par degradado, y después dispara el pruning simulado.

## Requisitos

- Docker + Docker Compose v2 (`docker compose version`)
- Conexión a internet la primera vez (para bajar las imágenes `python:3.12-slim` y `alpine:3.20`)

No hace falta ninguna cuenta, credencial ni cliente Ethereum real.

## Cómo correrlo

```bash
cd automatizacion-nodos-blockchain
docker compose up --abort-on-container-exit --exit-code-from monitor
```

Al terminar, limpiar los contenedores:

```bash
docker compose down -v
```

## Salida esperada

El contenedor `monitor` imprime algo equivalente a esto (timestamps van a variar):

```
monitor-1  | === Health check: nodo healthy ===
monitor-1  | OK [healthy]: cliente de ejecucion con 8 peers
monitor-1  | OK [healthy]: beacon node saludable y sincronizado
monitor-1  | 2026-08-20 14:47:22 - [healthy] todos los checks pasaron
monitor-1  |
monitor-1  | === Health check: nodo degraded (peers insuficientes + beacon no saludable) ===
monitor-1  | WARNING [degraded]: solo 1 peers conectados (minimo: 3)
monitor-1  | CRITICAL [degraded]: beacon node reporta estado no saludable (HTTP 503)
monitor-1  | 2026-08-20 14:47:22 - [degraded] health check fallido con 2 errores
monitor-1  |
monitor-1  | === Demo de auto-pruning por umbral de disco ===
monitor-1  | 2026-08-20 14:47:22 - Uso simulado de disco en /scripts/demo-data: 150% (limite 10MB)
monitor-1  | 2026-08-20 14:47:22 - Umbral de 80% superado. Iniciando pruning...
monitor-1  |   -> systemctl stop ethereum-execution   (simulado)
monitor-1  |   -> pruning /scripts/demo-data/file1.dat
monitor-1  |   -> pruning /scripts/demo-data/file2.dat
monitor-1  |   -> pruning /scripts/demo-data/file3.dat
monitor-1  |   -> systemctl start ethereum-execution  (simulado)
monitor-1  | 2026-08-20 14:47:22 - Pruning completado. Uso final: 60%
monitor-1  exited with code 0
```

El nodo "healthy" pasa los dos checks. El nodo "degraded" (1 peer, beacon con HTTP 503 y sincronizando) falla ambos, tal como haría el `health-check.sh` real contra un nodo con problemas de peers o un beacon caído. El bloque de pruning genera 5 archivos de 3MB (15MB contra un límite simulado de 10MB = 150%), supera el umbral del 80% y borra los 3 archivos más antiguos hasta bajar del umbral (60%).

## Archivos

| Archivo | Rol |
|---|---|
| `mock_node_server.py` | Servidor HTTP mínimo que simula las respuestas JSON-RPC/REST de un nodo Ethereum (ejecución y consenso), configurable por variables de entorno (`PEERS`, `SYNCING`, `HEALTH_CODE`). |
| `health-check.sh` | Health check de ejecución + consenso, calcado del script del post, parametrizado con `EXEC_RPC` / `BEACON_API` / `MIN_PEERS`. |
| `auto-prune-demo.sh` | Versión demostrable del auto-pruning por umbral de disco del post. |
| `docker-compose.yml` | Orquesta los 4 mocks y el monitor que corre los dos scripts. |

## Llevarlo a producción

Para usar esto contra un nodo real, solo hay que cambiar:

- `EXEC_RPC` / `BEACON_API` en `health-check.sh` para que apunten al `localhost:8545` / `localhost:5052` reales del nodo, y registrarlo como `systemd` timer (ver `ethereum-prune.timer` en el post) o como *liveness probe* si corre en Kubernetes.
- `auto-prune-demo.sh` por el `scripts/auto-prune.sh` original del post, que usa `df` sobre el disco real y `geth snapshot prune-state` en vez de `rm`.
