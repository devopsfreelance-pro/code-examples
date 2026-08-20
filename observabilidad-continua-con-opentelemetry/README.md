# Observabilidad continua con OpenTelemetry - ejemplo ejecutable

Post relacionado: [OpenTelemetry: Guía Práctica de Observabilidad Continua](https://www.devopsfreelance.pro/blog/posts/observabilidad-continua-con-opentelemetry/)

## Qué demuestra

El post explica que la potencia de OpenTelemetry aparece cuando una traza
cruza varios servicios y se correlaciona automáticamente sin escribir código
de propagación a mano, y menciona un caso real de e-commerce: el checkout se
vuelve lento cuando el pedido trae múltiples cupones aplicados, algo que las
métricas promedio no revelan pero una traza distribuida sí.

Este ejemplo reproduce ese caso con dos servicios Flask reales:

- **`checkout-service`** (puerto 5000): recibe la request de checkout y llama
  por HTTP a `coupon-service`.
- **`coupon-service`** (puerto 5001): valida cada cupón recibido, con un costo
  fijo por cupón (0.3s). Con 1 cupón no se nota; con 4 o 5, el tiempo se
  acumula y aparece como un pico de latencia.
- Ambos servicios usan instrumentación automática de `requests` y `flask`
  (`opentelemetry-instrumentation-requests` / `-flask`): el header
  `traceparent` se propaga solo entre el cliente HTTP de un servicio y el
  servidor del otro, sin tocar código de negocio.
- El **OpenTelemetry Collector** (`otel-collector-config.yaml`) recibe los
  spans de ambos servicios vía OTLP gRPC, los procesa con `memory_limiter` +
  `batch`, y los exporta a **Jaeger** (arquitectura Collector-como-gateway
  descrita en el post) y a los logs del propio Collector (exporter `debug`).
- **Jaeger UI** permite ver la traza completa `checkout-service ->
  coupon-service` con los spans hijos `validar-cupon` por cada cupón, tal
  como se describe en el caso de uso del post.

## Requisitos

- Docker y Docker Compose (plugin `docker compose` o binario `docker-compose`)
- Puertos libres en el host: `4317`, `4318`, `4319`, `5000`, `5001`, `16686`

## Cómo correrlo

```bash
cd observabilidad-continua-con-opentelemetry
docker compose up --build
```

Esperá a que los cuatro servicios (`jaeger`, `otel-collector`,
`coupon-service`, `checkout-service`) terminen de arrancar (unos 15-20
segundos la primera vez, por el build de las imágenes).

Generá dos checkouts, uno con un solo cupón y otro con varios, para comparar
la latencia:

```bash
# Checkout rápido: 1 cupón
time curl -s "http://localhost:5000/checkout?cupones=DESCUENTO10" | python3 -m json.tool

# Checkout lento: 5 cupones acumulados
time curl -s "http://localhost:5000/checkout?cupones=A10,B20,C5,D15,E25" | python3 -m json.tool
```

Salida esperada del segundo request:

```json
{
    "checkout": "aprobado",
    "cupones_validados": ["A10", "B20", "C5", "D15", "E25"],
    "todos_validos": true
}
```

Y en la terminal, el `time` real debería mostrar una diferencia clara: cerca
de 0.3s para el primer checkout contra cerca de 1.5s para el segundo (5
cupones x 0.3s cada uno).

Abrí Jaeger UI en el navegador:

```
http://localhost:16686
```

En el selector **Service** elegí `checkout-service`, click en **Find
Traces**, y abrí la traza más reciente con 5 spans `validar-cupon`. Vas a ver
un único trace ID que agrupa el span `checkout` (servicio checkout-service) y
el span `validar-cupones` con sus 5 hijos `validar-cupon` (servicio
coupon-service), con los tiempos apilados uno tras otro: exactamente el
patrón de latencia que las métricas agregadas no muestran y que la traza
distribuida sí revela.

Para bajar todo:

```bash
docker compose down
```

## Notas

- Este ejemplo usa el exporter `debug` del Collector además de Jaeger: si
  querés ver los spans crudos en texto, corré
  `docker compose logs otel-collector` mientras generás tráfico.
- El puerto OTLP gRPC de Jaeger se mapea al host como `4319` (en vez de
  `4317`) para no chocar con el puerto que expone el propio Collector; la
  comunicación interna Collector -> Jaeger usa el puerto real `4317` dentro
  de la red de Docker Compose, así que esto no afecta el funcionamiento.
