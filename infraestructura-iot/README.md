# Infraestructura IoT: broker MQTT + filtrado en el edge

Post relacionado: [Los 7 Secretos para Dominar Infraestructura IoT en DevOps](https://www.devopsfreelance.pro/blog/posts/infraestructura-iot/)

## Que demuestra este ejemplo

El post describe una arquitectura de referencia con capas de dispositivos,
red, edge computing y plataforma cloud, donde el edge filtra y agrega
datos antes de enviarlos a la nube (ver seccion "Capa de Edge Computing").
Este ejemplo reproduce esa arquitectura en miniatura, corriendo todo en
Docker en tu máquina, sin cuenta de AWS ni de ningún cloud:

- **`mosquitto`**: broker MQTT (capa de red), el mismo protocolo que usa
  el post en el ejemplo de ESP32.
- **`sensor-simulator`**: simula 3 sensores de temperatura (capa de
  dispositivos) que publican una lectura cada 3 segundos en
  `sensors/temperature/<device_id>`. De vez en cuando genera un pico
  térmico para poder ver el filtrado en accion.
- **`edge-processor`**: gateway de edge computing. Se suscribe a todas
  las lecturas y aplica la misma lógica que el ejemplo Node.js/AWS
  Greengrass del post: si la temperatura supera el umbral (30°C por
  defecto), reenvía una alerta a `cloud/alerts/temperature`; si no,
  la guarda localmente y cada 20 segundos publica un resumen agregado
  en `cloud/summaries/periodic` en vez de reenviar cada lectura cruda.
- **`cloud-monitor`**: simula la plataforma cloud IoT. Solo se suscribe
  a `cloud/#`, así que en su log se ve claramente que llega mucho menos
  tráfico del que generan los sensores: esa reducción de volumen es el
  punto central de hacer edge computing.

## Requisitos

- Docker y Docker Compose (`docker compose version` para verificar).
- Ningún servicio de pago ni cuenta cloud: todo corre localmente.

## Pasos para correrlo

```bash
cd infraestructura-iot
docker compose up --build
```

Dejalo corriendo un par de minutos. Vas a ver logs intercalados de los
4 contenedores. Para verlos por separado, en otras terminales:

```bash
docker compose logs -f sensor-simulator
docker compose logs -f edge-processor
docker compose logs -f cloud-monitor
```

Para parar y limpiar:

```bash
docker compose down
```

## Salida esperada

En `sensor-simulator` vas a ver una lectura publicada cada 3 segundos
por cada uno de los 3 sensores, por ejemplo:

```
[simulator] sensors/temperature/temp-001 -> 21.87C
[simulator] sensors/temperature/temp-002 -> 34.52C
[simulator] sensors/temperature/temp-003 -> 22.10C
```

En `edge-processor` vas a ver que la mayoría de las lecturas quedan
almacenadas localmente, y solo las que superan el umbral generan una
alerta inmediata:

```
[edge] dato normal almacenado localmente: temp-001 = 21.87C
[edge] ALERTA enviada a la nube: temp-002 = 34.52C (> 30.0C)
[edge] dato normal almacenado localmente: temp-003 = 22.1C
...
[edge] resumen periodico enviado a la nube: {"timestamp": ..., "devices": {"temp-001": {"count": 6, "avg_temperature": 22.3, ...}}}
```

En `cloud-monitor` solo vas a ver las alertas y los resúmenes
periódicos, nunca el stream crudo de sensores:

```
[cloud] recibido en cloud/alerts/temperature: {"device_id": "temp-002", "temperature": 34.52, ...}
[cloud] recibido en cloud/summaries/periodic: {"timestamp": ..., "devices": {...}}
```

Esa diferencia de volumen entre lo que publica `sensor-simulator` y lo
que efectivamente llega a `cloud-monitor` es, en miniatura, la razón
por la que el post recomienda procesar en el edge antes de enviar a la
nube.

## Ajustar el comportamiento

Variables de entorno definidas en `docker-compose.yml`:

- `PUBLISH_INTERVAL_SECONDS` (sensor-simulator): frecuencia de publicación.
- `TEMPERATURE_THRESHOLD` (edge-processor): umbral de alerta en °C.
- `SUMMARY_INTERVAL_SECONDS` (edge-processor): cada cuánto se agrega y
  envía el resumen.
