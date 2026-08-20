# Monitoreo con OpenTelemetry - ejemplo ejecutable

Post relacionado: [Guía Completa de Monitoreo con OpenTelemetry](https://www.devopsfreelance.pro/blog/posts/monitoreo-con-opentelemetry/)

## Qué demuestra

Un flujo completo de observabilidad con OpenTelemetry corriendo en local:

- Una API Flask (`app/app.py`) instrumentada manualmente, igual que el ejemplo
  `procesar_pedido` del post: crea un span padre (`procesar-pedido`) con dos
  spans hijos (`validar-pedido` y `procesar-pago`), les agrega atributos
  (`pedido.id`, `pago.estado`) y además emite una métrica de negocio
  (`pedidos_procesados_total`) usando el SDK de OTel.
- El **OpenTelemetry Collector** (`otel-collector-config.yaml`) recibiendo
  trazas y métricas vía OTLP gRPC/HTTP, procesándolas con `memory_limiter` y
  `batch`, y enrutándolas: las trazas al exporter `debug` (se ven en los logs
  del contenedor) y las métricas al exporter `prometheus`.
- **Prometheus** (`prometheus.yml`) scrapeando las métricas que expone el
  Collector en `:8889`.

Con esto se ve en la práctica la arquitectura del post: aplicación
instrumentada -> Collector -> backends, sin tocar código de negocio para
cambiar de backend.

## Requisitos

- Docker y Docker Compose (plugin `docker compose` o binario `docker-compose`)
- Puertos libres en el host: `4317`, `4318`, `5000`, `8889`, `9090`

## Cómo correrlo

```bash
cd monitoreo-con-opentelemetry
docker compose up --build
```

Esperá a que los tres servicios (`otel-collector`, `prometheus`, `app`)
terminen de arrancar (unos 10-15 segundos).

Generá tráfico contra la API de pedidos:

```bash
for i in 1 2 3 4 5; do
  curl -s http://localhost:5000/pedido/$i | python3 -m json.tool
done
```

Salida esperada por cada request:

```json
{
    "estado": "aprobado",
    "pedido_id": "1"
}
```

### Ver las trazas

Las trazas se exportan con el exporter `debug` del Collector, así que
aparecen en su log:

```bash
docker compose logs otel-collector | grep -A 5 "procesar-pedido"
```

Vas a ver el span `procesar-pedido` con sus atributos (`pedido.id`,
`pedido.tipo`) y sus spans hijos `validar-pedido` y `procesar-pago`,
todos compartiendo el mismo `TraceID`.

### Ver las métricas

Prometheus queda disponible en http://localhost:9090. Buscá la métrica:

```
otel_pedidos_procesados_total
```

También podés consultar el endpoint crudo que expone el Collector:

```bash
curl -s http://localhost:8889/metrics | grep pedidos_procesados
```

Salida esperada (el valor sube con cada request a `/pedido/<id>`):

```
otel_pedidos_procesados_total{pedido_tipo="ecommerce"} 5
```

## Apagar el entorno

```bash
docker compose down
```

## Estructura

```
monitoreo-con-opentelemetry/
├── docker-compose.yml           # orquesta collector + prometheus + app
├── otel-collector-config.yaml   # receivers/processors/exporters del Collector
├── prometheus.yml                # scrape config de Prometheus
└── app/
    ├── Dockerfile
    └── app.py                    # API Flask instrumentada con OTel
```

## Notas

- No se incluye Jaeger para mantener el ejemplo mínimo; el exporter `debug`
  del Collector alcanza para ver las trazas y su correlación por `TraceID`.
  Para agregar Jaeger, sumá un exporter `otlp/jaeger` al pipeline `traces` en
  `otel-collector-config.yaml` y un servicio `jaeger` (imagen
  `jaegertracing/all-in-one`) al `docker-compose.yml`, como se muestra en el
  post original.
- No se usan credenciales ni servicios pagos: todo corre con imágenes
  públicas (`otel/opentelemetry-collector-contrib`, `prom/prometheus`) sobre
  Docker local.
