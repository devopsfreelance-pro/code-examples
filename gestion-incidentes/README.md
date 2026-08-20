# Gestion de Incidentes: deteccion, alerta y escalamiento con Prometheus + Alertmanager

Post relacionado: [Gestion de Incidentes: Proceso Completo para Equipos DevOps](https://www.devopsfreelance.pro/blog/posts/gestion-incidentes/)

## Que demuestra este ejemplo

El post describe el ciclo de gestion de incidentes: deteccion, clasificacion,
alerta, escalamiento y notificacion. Este ejemplo reproduce ese ciclo con
herramientas reales y locales, sin cuentas pagas:

1. Una app minima (`app.py`) expone una metrica Prometheus
   (`demo_api_error_rate`) que simula la tasa de error de una API.
2. **Prometheus** scrapea esa metrica y evalua una regla de alerta
   (`alert_rules.yml`) equivalente al ejemplo `API Error Rate High` del post
   (umbral, ventana de persistencia `for`, `summary` y `runbook` en las
   anotaciones).
3. Cuando la alerta pasa a estado `firing`, Prometheus se la envia a
   **Alertmanager**, que aplica una politica de ruteo/escalamiento
   (`alertmanager.yml`) equivalente al `escalation_policies` de PagerDuty del
   post, pero implementada con un webhook.
4. Alertmanager llama al webhook de `app.py`, que imprime en logs una
   notificacion de "escalamiento a on-call primario" con el resumen y el
   link al runbook, tal como describe el post en la fase de "Asignacion y
   Escalamiento".
5. Al resolver el incidente, Alertmanager notifica el estado `resolved` y
   el log lo refleja, cerrando el ciclo hasta el "Analisis Post-Incidente".

## Requisitos

- Docker y Docker Compose (plugin `docker compose`, no hace falta nada mas).
- Puertos libres en tu maquina: `8000`, `9000`, `9090`, `9093`.
- No se necesita cuenta de PagerDuty, Datadog ni ningun servicio pago: todo
  corre en contenedores locales.

## Como correrlo

1. Levantar la pila completa:

```bash
cd gestion-incidentes
docker compose up -d
```

2. Verificar que los tres servicios estan arriba:

```bash
docker compose ps
```

Deberias ver `incidentes-demo-app`, `incidentes-prometheus` y
`incidentes-alertmanager` en estado `running`.

3. Confirmar que Prometheus esta scrapeando la metrica sin incidente activo
   (tasa de error baja, sin alertas disparadas):

```bash
curl -s http://localhost:8000/metrics
```

Salida esperada:

```
# HELP demo_api_error_rate Tasa de error simulada de la API
# TYPE demo_api_error_rate gauge
demo_api_error_rate 0.01
```

4. Disparar un incidente simulado (tasa de error sube a 0.80, por encima
   del umbral 0.05 de la regla):

```bash
curl -X POST http://localhost:8000/trigger
```

5. Seguir los logs de la app para ver la deteccion y el escalamiento en
   tiempo real (Prometheus tarda hasta ~30s en confirmar la alerta por el
   `for: 30s` de la regla, mas el `group_wait` de Alertmanager):

```bash
docker compose logs -f demo-app
```

Salida esperada (aparece entre ~30 y ~50 segundos despues del `trigger`):

```
incidentes-demo-app  | 2026-08-20T12:00:00Z INCIDENTE SIMULADO: error_mode=ON (demo_api_error_rate=0.80)
incidentes-demo-app  | 2026-08-20T12:00:45Z [ESCALAMIENTO] Notificando a ingeniero on-call primario -> alerta=APIErrorRateHigh severity=critical resumen='Alta tasa de errores en la API (80.0%)' runbook=https://runbooks.example.com/api-errors
```

6. (Opcional) Ver la alerta tambien desde las UIs web:
   - Prometheus: http://localhost:9090/alerts (estado `firing`)
   - Alertmanager: http://localhost:9093 (alerta agrupada, receptor
     `demo-webhook`)

7. Resolver el incidente:

```bash
curl -X POST http://localhost:8000/resolve
```

En los logs de `demo-app` va a aparecer la notificacion de resolucion:

```
incidentes-demo-app  | 2026-08-20T12:01:00Z INCIDENTE RESUELTO: error_mode=OFF (demo_api_error_rate=0.01)
incidentes-demo-app  | 2026-08-20T12:01:40Z [RESUELTO] alerta=APIErrorRateHigh status=resolved
```

8. Apagar todo:

```bash
docker compose down
```

## Notas sobre los tiempos

En produccion, la regla del post usa `for: 5m` (evitar alertas por picos
momentaneos) y PagerDuty escala cada 15-30 minutos entre niveles. Para poder
ver el ciclo completo en una demo de unos minutos, este ejemplo acorta esos
tiempos (`for: 30s`, `group_wait: 10s`, `repeat_interval: 1m`) en
`alert_rules.yml` y `alertmanager.yml`. Ajustalos a los valores reales si
usas este ejemplo como base para un entorno productivo.
