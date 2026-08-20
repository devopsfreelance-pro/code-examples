# Reliability testing: SLO validation + chaos experiment con circuit breaker

Post relacionado: [Guía Completa de Reliability testing](https://www.devopsfreelance.pro/blog/posts/reliability-testing/)

## Qué demuestra este ejemplo

El post explica dos técnicas centrales del reliability testing: validar un
despliegue contra SLOs (disponibilidad y latencia) y usar fault injection
para comprobar que un circuit breaker se activa ante fallos consecutivos.

Este ejemplo las implementa contra un servicio real corriendo en Docker,
en vez de simularlas con funciones mockeadas:

- `app.py`: un servicio Flask con `/health` que puede degradarse en
  caliente (tasa de fallos y latencia inyectada) a través de un endpoint
  de administración `/admin/chaos`, simulando un experimento de chaos
  engineering.
- `reliability_test.py`: golpea `/health` durante N segundos y valida el
  resultado contra un SLO de success rate y de latencia p95 (equivalente
  local, sin Datadog, del script `validate_deployment_reliability` del
  post).
- `chaos_test.py`: inyecta una tasa de fallos alta vía `/admin/chaos` y
  verifica que un circuit breaker "cliente" se activa tras N fallos
  consecutivos (equivalente del ejemplo `test_circuit_breaker_activation`
  del post, pero contra un servicio real).

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- Python 3.10+ con el paquete `requests` instalado en el host
  (`pip install requests`), para correr los scripts de prueba desde fuera
  del contenedor

No requiere cuentas de terceros ni servicios pagos.

## Pasos para correrlo

### 1. Levantar el servicio objetivo

```bash
cd reliability-testing
docker compose up -d --build
```

Verificar que responde:

```bash
curl http://localhost:5000/health
# {"status":"ok"}
```

### 2. Ejecutar el reliability test contra el servicio sano

```bash
python3 reliability_test.py --duration 10 --interval 0.5 \
  --slo-success-rate 0.95 --slo-latency 0.3
```

Salida esperada (el servicio arranca sin fallos inyectados, así que
cumple el SLO):

```
Ejecutando reliability test durante 10s contra http://localhost:5000/health ...
Peticiones totales : 20
Success rate       : 100.00%
Latencia p95       : 0.004s
OK: el servicio cumple con los SLOs definidos
```

### 3. Ejecutar el experimento de chaos engineering

```bash
python3 chaos_test.py --failure-rate 0.9 --threshold 4
```

El script inyecta una tasa de fallos del 90% en el servicio, verifica que
el "circuit breaker" del cliente se activa tras 4 fallos consecutivos, y
al final restaura el servicio a su estado sano (`/admin/reset`):

```
Inyectando fallos: failure_rate=0.9, latency_ms=0
Intento 1: fallos consecutivos = 1
Intento 2: fallos consecutivos = 2
Intento 3: fallos consecutivos = 3
Intento 4: fallos consecutivos = 4
Restaurando el servicio a estado sano...
OK: el circuit breaker se activo tras 4 fallos consecutivos
```

### 4. Confirmar que el servicio volvió a estar sano

```bash
curl http://localhost:5000/health
# {"status":"ok"}
```

### 5. Apagar el servicio

```bash
docker compose down
```

## Notas

- `failure_rate` y `latency_ms` son parámetros que ambos scripts pasan al
  endpoint `/admin/chaos`; no hay secretos ni credenciales involucradas.
- Este ejemplo es intencionalmente mínimo: ilustra el patrón central del
  post (validar contra SLOs + fault injection con verificación de circuit
  breaker), no una suite completa de reliability testing de producción.
