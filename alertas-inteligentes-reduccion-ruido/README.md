# Alert routing, agrupamiento e inhibicion con Alertmanager

Post: [Alert Fatigue: Guía Completa para Reducir el Ruido](https://www.devopsfreelance.pro/blog/posts/alertas-inteligentes-reduccion-ruido/)

## Que demuestra este ejemplo

El post describe varias tecnicas de noise reduction monitoring: agrupar
alertas correlacionadas en una sola notificacion, suprimir alertas
redundantes cuando ya hay una critica activa para el mismo componente, y
enrutar cada severidad a un canal distinto. Este ejemplo implementa esas
tres ideas con [Prometheus Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/)
real, sin Prometheus scrapeando nada: las alertas se inyectan directo a la
API de Alertmanager para poder observar el comportamiento en segundos.

Levanta:

- **Alertmanager**, configurado con `alertmanager/alertmanager.yml`:
  - `route` con arbol de enrutamiento por `severity` (critical / high / low),
    cada rama con su propio `group_wait` / `group_interval` / `repeat_interval`.
  - `group_by: [alertname, service]`: varias alertas del mismo problema se
    agrupan en una sola notificacion.
  - `inhibit_rules`: una alerta `critical` suprime las `high`/`low` del
    mismo `service` (evita las "50 alertas de backend inaccesible" cuando
    el problema real es el balanceador).
- Un **receptor de webhooks** minimo (`receiver/receiver.py`, solo stdlib de
  Python) que escucha en 3 puertos, uno por canal (`critical`, `high`,
  `default`), simulando que cada severidad va a un canal de notificacion
  distinto.
- `send_alerts.sh`, que envia alertas de prueba a la API de Alertmanager
  para disparar los dos escenarios (agrupamiento e inhibicion).

## Requisitos

- Docker y Docker Compose (plugin `docker compose`).
- `curl` (para el script de prueba).
- Sin cuentas ni credenciales: todo corre en local.

## Pasos para correrlo

```bash
cd alertas-inteligentes-reduccion-ruido

# 1. Levantar Alertmanager + el receptor de webhooks
docker compose up -d

# 2. Confirmar que Alertmanager cargo la config sin errores
curl -s http://localhost:9093/-/ready
# -> OK

# 3. En otra terminal, seguir los logs del receptor (dejalo abierto)
docker compose logs -f receiver

# 4. En la terminal original, disparar los dos escenarios de prueba
./send_alerts.sh
```

## Salida esperada

En los logs de `receiver` deberian aparecer dos notificaciones (verificado
al construir este ejemplo):

**Escenario 1 (agrupamiento):** 5 alertas `BackendUnavailable` de distintas
instancias de `checkout` se envian por separado, pero Alertmanager las junta
por `group_by: [alertname, service]` y el canal `high` recibe **una sola**
notificacion con las 5 adentro:

```
=== Notificacion recibida en canal 9092 ===
Canal: HIGH     -> Slack con mencion
Alertas agrupadas en este envio: 5
  - alertname=BackendUnavailable service=checkout severity=high status=firing
  - alertname=BackendUnavailable service=checkout severity=high status=firing
  - alertname=BackendUnavailable service=checkout severity=high status=firing
  - alertname=BackendUnavailable service=checkout severity=high status=firing
  - alertname=BackendUnavailable service=checkout severity=high status=firing
```

**Escenario 2 (inhibicion):** se envia una alerta `critical` (`DatabaseDown`,
`service=payments`), que si llega al canal `critical`:

```
=== Notificacion recibida en canal 9091 ===
Canal: CRITICAL -> llamada/SMS (interrumpe ya)
Alertas agrupadas en este envio: 1
  - alertname=DatabaseDown service=payments severity=critical status=firing
```

Segundos despues se envia una alerta `high` (`HighLatency`, mismo
`service=payments`). Esa **no** debe aparecer en el canal `high`: la regla
`inhibit_rules` la suprime porque ya hay una `critical` activa para el mismo
`service`. Podes confirmarlo viendo que Alertmanager la reconoce como
inhibida:

```bash
curl -s http://localhost:9093/api/v2/alerts | python3 -m json.tool
# la alerta HighLatency aparece con status.state = "suppressed"
```

## Limpiar

```bash
docker compose down -v
```

## Llevarlo a un caso real

- Reemplazar los `webhook_configs` de `alertmanager.yml` por integraciones
  reales (PagerDuty, Opsgenie, Slack) segun severidad.
- Alimentar Alertmanager desde Prometheus real (`rule_files` con `for:` para
  las ventanas de tiempo del post, y `rate()` para alertar por tasa de
  cambio en vez de umbral fijo) en lugar de inyectar alertas a mano.
- Ajustar `equal` en `inhibit_rules` para que coincida con las labels reales
  de tu topologia de servicios (por ejemplo `cluster`, `namespace`).
