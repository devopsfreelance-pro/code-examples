# Observabilidad microservicios: tracing distribuido con OpenTelemetry + Jaeger

Ejemplo de codigo del post [Guia Completa de Observabilidad](https://www.devopsfreelance.pro/blog/posts/observabilidad/).

## Que demuestra

Dos microservicios Flask (`order-service` y `payment-service`) instrumentados
con el SDK de OpenTelemetry, tal como se describe en el post. `order-service`
recibe una peticion en `/process-payment` y llama por HTTP a `payment-service`,
que valida el pago en un span manual. Ambos exportan sus spans via OTLP/gRPC
a un **OpenTelemetry Collector**, que a su vez los reenvia a **Jaeger**.

El resultado: una unica traza distribuida visible en la UI de Jaeger que
conecta los spans de los dos servicios, con la propagacion de contexto
(W3C Trace Context) ocurriendo automaticamente gracias a la
auto-instrumentacion de `requests` y `flask`.

Esto reproduce en miniatura la arquitectura descripta en el post: apps
instrumentadas -> Collector (batch + export) -> Jaeger.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- Puertos libres en tu maquina: `5000` (order-service) y `16686` (Jaeger UI)

## Pasos para correrlo

```bash
cd observabilidad
docker compose up --build
```

Esperá a ver en los logs que los tres servicios (`otel-collector`, `jaeger`,
`payment-service`, `order-service`) arrancaron sin errores (unos 10-15
segundos).

En otra terminal, generá una traza haciendo una peticion al servicio de
ordenes:

```bash
curl http://localhost:5000/process-payment
```

Salida esperada (el campo `validated` puede ser `true` o `false`, es
aleatorio a proposito para simular tanto el camino feliz como el de error):

```json
{"order_id": "order-12345", "payment": {"validated": true}}
```

Repetí el `curl` varias veces para generar varias trazas, incluyendo alguna
con error (aprox. 1 de cada 5 llamadas falla la validacion a proposito).

Abrí la UI de Jaeger en el navegador:

```
http://localhost:16686
```

- En el selector "Service", elegí `order-service`.
- Click en "Find Traces".
- Abrí una traza: vas a ver dos spans conectados, `process-order-payment`
  (order-service) y `validate-payment-details` (payment-service), con sus
  atributos (`order.id`, `payment.amount`, `validation.status`, etc.) y,
  en las trazas con error, el span de payment-service marcado en rojo.

Para apagar todo:

```bash
docker compose down
```

## Estructura

```
observabilidad/
├── docker-compose.yml            # Jaeger + Collector + los 2 microservicios
├── otel-collector-config.yaml    # Pipeline OTLP -> batch -> Jaeger (igual al del post, adaptado a Compose)
└── app/
    ├── Dockerfile
    ├── requirements.txt
    ├── tracing_setup.py          # Inicializacion comun del TracerProvider (Resource + OTLP exporter)
    ├── order_service.py          # Servicio de entrada, llama a payment-service
    └── payment_service.py        # Servicio downstream, valida el pago con un span manual
```

## Notas

- No requiere ninguna cuenta ni credencial externa: todo corre local con
  contenedores (Jaeger `all-in-one` usa almacenamiento en memoria, pensado
  solo para desarrollo/demo, no para produccion).
- El `otel-collector-config.yaml` de este ejemplo es una version simplificada
  para Docker Compose del ConfigMap que aparece en el post para Kubernetes
  (mismo concepto: receiver OTLP, processor `batch`, exporter hacia Jaeger).
