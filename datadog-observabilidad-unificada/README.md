# Datadog APM: trazabilidad distribuida en un servicio de pagos

Ejemplo de codigo que acompaña al post
[Datadog: Plataforma Unificada de Observabilidad 2025](https://www.devopsfreelance.pro/blog/posts/datadog-observabilidad-unificada/).

## Que demuestra

El post explica que Datadog unifica metricas, trazas (APM) y logs mediante
el Datadog Agent y el tagging multidimensional. Este mini-ejemplo reproduce
el nucleo de esa arquitectura con un servicio real:

- Un microservicio Flask (`payment-service`) instrumentado con **ddtrace**,
  la libreria de APM de Datadog usada en el snippet del post
  (`@tracer.wrap`, spans manuales, tags personalizados).
- Un contenedor con el **Datadog Agent** (`datadog-agent`) recibiendo esas
  trazas por el puerto 8126, tal como describe la seccion de arquitectura
  del post (agente ligero que recolecta y reenvia datos a la plataforma).
- Tags de entorno (`env:demo`), servicio (`service:payment-service`) y
  version (`DD_VERSION`) aplicados igual que el post recomienda para poder
  filtrar y correlacionar datos.

Al llamar al endpoint `/pay`, la app genera 3 spans encadenados
(`process_payment` -> `validate_card` -> `charge_amount`) que se pueden ver
en Datadog APM como una traza distribuida completa, incluyendo un caso de
error (monto invalido) para ver como se marca `error=true` en un span.

## Requisitos

- Docker y Docker Compose.
- Una cuenta de Datadog (el [trial gratuito de 14 dias](https://www.datadoghq.com/free-datadog-trial/)
  alcanza) para obtener una **API key** y ver las trazas en la UI real de
  Datadog APM. Sin la API key, el ejemplo igual corre localmente (la app
  responde y genera trazas), pero el Datadog Agent no podra reenviarlas a
  la plataforma.

## Variables de entorno inevitables (secretos)

- `DD_API_KEY`: API key de tu cuenta de Datadog (Organization Settings ->
  API Keys). Nunca la commitees, se pasa por variable de entorno.
- `DD_SITE`: opcional, region de tu cuenta (`datadoghq.com`, `datadoghq.eu`,
  etc). Default `datadoghq.com`.

## Pasos para correrlo

1. Exportar la API key (reemplazar por la tuya):

```bash
export DD_API_KEY=tu_api_key_de_datadog
```

2. Levantar el stack:

```bash
docker compose up --build
```

3. En otra terminal, generar un pago exitoso:

```bash
curl -s -X POST http://localhost:5000/pay \
  -H "Content-Type: application/json" \
  -d '{"amount": 150.5, "user_id": "user-42"}'
```

Salida esperada:

```json
{"amount":150.5,"status":"approved","user_id":"user-42"}
```

4. Generar un pago rechazado (para ver un span con error):

```bash
curl -s -X POST http://localhost:5000/pay \
  -H "Content-Type: application/json" \
  -d '{"amount": 0, "user_id": "user-42"}'
```

Salida esperada:

```json
{"error":"El monto debe ser mayor a 0","status":"rejected"}
```

5. Verificar que el servicio esta vivo:

```bash
curl -s http://localhost:5000/health
```

Salida esperada:

```json
{"status":"ok"}
```

6. Si configuraste `DD_API_KEY` valida, entra a **Datadog > APM > Traces**
   y filtra por `service:payment-service env:demo`. Deberias ver las trazas
   `process_payment` con sus spans hijos `validate_card` y `charge_amount`,
   igual que describe el post sobre correlacion y Service Map.

7. Apagar el stack:

```bash
docker compose down
```

## Estructura

```
datadog-observabilidad-unificada/
├── docker-compose.yml   # Datadog Agent + payment-service
├── app/
│   ├── app.py            # Flask API instrumentada con ddtrace
│   ├── requirements.txt
│   └── Dockerfile
└── README.md
```
