# On-Call Best Practices: ruteo de alertas por severidad

Post relacionado: [Guía Completa de On-call best practices](https://www.devopsfreelance.pro/blog/posts/on-call-best-practices/)

## Qué demuestra este ejemplo

El post explica que las alertas mal diseñadas generan fatiga y burnout, y que
la clave es rutear cada alerta al canal correcto segun su severidad (critica
vs. advertencia), tal como muestra el ejemplo de configuracion de Prometheus
Alertmanager del articulo.

Este mini-laboratorio levanta una pila real con Docker Compose:

- **Prometheus** evalua dos reglas de alerta de demostracion (`rules.yml`):
  una `critical` (simula un incidente que debe despertar a la persona de
  guardia) y una `warning` (simula ruido de baja prioridad).
- **Alertmanager** (`alertmanager.yml`) rutea cada severidad a un receiver
  distinto, agrupa alertas relacionadas (`group_by`) y aplica `group_wait` /
  `repeat_interval` para reducir el ruido, igual que en el post.
- Un **webhook receptor** (`mendhak/http-https-echo`) hace de "PagerDuty" y
  "Slack" locales: solo imprime en su log el payload JSON que reciba en cada
  ruta (`/critical`, `/warning`, `/default`), asi se puede ver exactamente
  que le llega a cada canal sin necesitar cuentas pagas.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- Puertos libres en el host: `9090` (Prometheus), `9093` (Alertmanager),
  `8080` (webhook receptor)

## Pasos para ejecutarlo

```bash
cd on-call-best-practices
docker compose up -d
```

Esperar unos 30 segundos a que las reglas evaluen (`for: 15s` / `for: 30s`)
y despues revisar:

```bash
# Ver las alertas activas en Prometheus
open http://localhost:9090/alerts
# (o: curl -s http://localhost:9090/api/v1/alerts | jq)

# Ver el estado de ruteo en Alertmanager
open http://localhost:9093
# (o: curl -s http://localhost:9093/api/v2/alerts | jq)

# Ver el payload que recibio cada canal (critico vs warning)
docker compose logs webhook-receiver --since 2m
```

## Salida esperada

En `docker compose logs webhook-receiver` deberian aparecer al menos dos
requests `POST` separados, uno a `/critical` con `"severity":"critical"` y
`"alertname":"SyntheticCriticalIncident"` en el body, y otro a `/warning`
con `"severity":"warning"` y `"alertname":"SyntheticWarningNoise"`. Eso
confirma que Alertmanager separo correctamente ambos canales en vez de
mandar todo al mismo lugar (el problema de "alertas ruidosas" que describe
el post).

En `http://localhost:9090/alerts` ambas alertas deben verse en estado
`firing` (rojas), y en `http://localhost:9093` deben aparecer agrupadas por
`alertname` + `severity`.

Para apagar todo:

```bash
docker compose down
```

## Nota sobre datos falsos

`pagerduty-critical` y `slack-warnings` en `alertmanager.yml` apuntan al
webhook local en lugar de `pagerduty_configs` / `slack_configs` reales, para
que el ejemplo corra sin cuentas de terceros. En produccion, reemplazar esos
receivers por los del post original (con `service_key` de PagerDuty o
`api_url` de un Incoming Webhook de Slack, ambos guardados como secreto, no
en el YAML).
