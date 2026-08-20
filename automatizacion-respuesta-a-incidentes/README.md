# Automatización de Respuesta a Incidentes — Ejemplo Ejecutable

Post: [Automatización de Respuesta a Incidentes: Guía Práctica DevOps](https://www.devopsfreelance.pro/blog/posts/automatizacion-respuesta-a-incidentes/)

## Qué demuestra

Un motor mínimo de automatización de respuesta a incidentes que recibe alertas
con formato compatible con **Alertmanager** (webhook `POST /webhook/alert`) y
aplica el ciclo descripto en el post:

1. **Detección**: recibe la alerta vía webhook.
2. **Clasificación**: severidad (`critical`/`warning`) y si existe runbook para ese `alertname`.
3. **Respuesta automática**: ejecuta un runbook (`restart_service` o `scale_out`) si corresponde.
4. **Escalamiento**: notifica a "on-call" (mock) cuando no hay runbook, se agota el
   límite de acciones, o la severidad es crítica.
5. **Buenas prácticas del post implementadas**:
   - **Idempotencia**: no repite la acción si el incidente sigue `firing` y ya fue mitigado.
   - **Límites duros / circuit breaker**: máximo N acciones por alerta por hora (`MAX_ACTIONS_PER_HOUR`).
   - **Modo dry-run**: con `DRY_RUN=true` solo registra qué haría, sin ejecutar nada.
   - **Logging detallado**: cada evento se loguea en JSON estructurado (timestamp, alerta, decisión, resultado).

No es un sistema de producción: es una demostración compacta de la lógica de
decisión que normalmente vive en un orquestador (Ansible, Rundeck, AWS SSM) o en
reglas de Alertmanager + un runner de runbooks.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- `curl` y `python3` (solo para el script de prueba, ya vienen en la mayoría de las distros)

## Cómo correrlo

1. Levantar el servicio:

   ```bash
   cd automatizacion-respuesta-a-incidentes
   docker compose up --build -d
   ```

2. Verificar que está arriba:

   ```bash
   curl http://localhost:5000/health
   ```

   Salida esperada:

   ```json
   {"dry_run": false, "max_actions_per_hour": 3, "status": "ok"}
   ```

3. Correr el script que simula alertas de Alertmanager:

   ```bash
   chmod +x send_test_alert.sh
   ./send_test_alert.sh
   ```

4. Ver el log estructurado de decisiones en tiempo real:

   ```bash
   docker compose logs -f incident-responder
   ```

## Salida esperada

El script `send_test_alert.sh` corre 5 escenarios y cada `curl` imprime el JSON
de respuesta del webhook. En los logs del contenedor (`docker compose logs`)
vas a ver líneas JSON como estas, en este orden:

```
{"event": "alert_received", "alertname": "ServiceDown", "severity": "critical", "status": "firing"}
{"event": "action_executed", "alertname": "ServiceDown", "action": "restart_service", "service": "checkout-api"}
{"event": "escalate", "alertname": "ServiceDown", "reason": "severidad critical, notificación informativa"}
{"event": "alert_received", "alertname": "ServiceDown", "severity": "critical", "status": "firing"}
{"event": "skip_idempotent", "alertname": "ServiceDown", "reason": "ya mitigado, esperando resolución"}
{"event": "alert_received", "alertname": "ServiceDown", "severity": "critical", "status": "resolved"}
{"event": "incident_resolved", "alertname": "ServiceDown"}
...
{"event": "escalate", "alertname": "HighCPULoad", "reason": "circuit breaker: demasiadas acciones en la última hora"}
...
{"event": "escalate", "alertname": "DiskAlmostFull", "reason": "sin runbook definido"}
```

Resumen de lo que se valida en cada paso del script:

| Paso | Alerta | Resultado esperado |
|---|---|---|
| 1 | `ServiceDown` firing | ejecuta `restart_service` |
| 2 | `ServiceDown` firing (repetida) | `skip_idempotent`, no repite la acción |
| 3 | `ServiceDown` resolved | limpia el estado del incidente |
| 4 | `HighCPULoad` firing/resolved x4 | 3 ejecutan `scale_out`, la 4ta escala por circuit breaker |
| 5 | `DiskAlmostFull` firing | escala directo a on-call (sin runbook definido) |

## Probar el modo dry-run

Editá `DRY_RUN=true` en `docker-compose.yml` (o exportá la variable y usá
`docker compose up -e DRY_RUN=true`) y volvé a levantar el servicio. Las
alertas van a loguearse como `{"event": "dry_run", ...}` sin marcar el
incidente como resuelto, tal como recomienda el post antes de confiar un
runbook nuevo a ejecución automática.

## Apagar el entorno

```bash
docker compose down
```

## Ir más allá

Este ejemplo no depende de servicios pagos ni cuentas externas. Para acercarlo
a un caso real, los siguientes pasos naturales (fuera del alcance de este demo)
serían: conectar `/webhook/alert` a un Alertmanager real, reemplazar las
acciones simuladas por llamadas a la API de Docker/Kubernetes, y cambiar
`escalate_to_oncall` por una llamada real a la API de Slack o PagerDuty.
