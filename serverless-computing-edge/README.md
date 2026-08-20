# Serverless Computing en Edge: demo de enrutamiento a funciones por region

Post relacionado: [Serverless Computing en Edge: Guía Definitiva para DevOps](https://www.devopsfreelance.pro/blog/posts/serverless-computing-edge/)

## Qué demuestra este ejemplo

El post explica el concepto central del serverless en edge: una función sin
estado se despliega en varios nodos cercanos al usuario y personaliza su
respuesta según la ubicación de quien la invoca (el mismo patrón que el
ejemplo de Cloudflare Worker del post, que responde distinto según
`CF-IPCountry`).

Este ejemplo reproduce esa arquitectura con contenedores locales:

- **3 "nodos edge"** (`edge-us`, `edge-eu`, `edge-sa`): cada uno corre la
  misma función serverless (`edge-node/app.py`, solo librería estándar de
  Python) pero representa una región distinta, igual que Cloudflare
  desplegaría el mismo Worker en múltiples Points of Presence.
- **Un gateway** (`nginx`, `gateway/nginx.conf`) que enruta cada petición al
  nodo edge correspondiente según el header `X-Edge-Region`, simulando cómo
  una CDN dirige al usuario al PoP más cercano.
- Cada respuesta incluye un mensaje personalizado por región y métricas
  simuladas (latencia de red y tiempo de ejecución de la función) para
  ilustrar la reducción de latencia que promete el edge computing.

## Requisitos

- Docker y Docker Compose
- `curl`

## Pasos para correrlo

1. Levantar los nodos edge y el gateway:

   ```bash
   docker compose up -d
   ```

2. Simular una petición desde Sudamérica:

   ```bash
   curl -s -H "X-Edge-Region: sa" http://localhost:8080/
   ```

   Salida esperada:

   ```json
   {
     "region": "sa",
     "edge_node_hostname": "a1b2c3d4e5f6",
     "message": "¡Hola desde el edge (Sudamerica)!",
     "simulated_network_latency_ms": 9,
     "function_exec_time_ms": 10.42
   }
   ```

3. Simular una petición desde Europa y desde Estados Unidos:

   ```bash
   curl -s -H "X-Edge-Region: eu" http://localhost:8080/
   curl -s -H "X-Edge-Region: us" http://localhost:8080/
   ```

   Cada respuesta trae `region` y `edge_node_hostname` distintos: el gateway
   enrutó la petición a un contenedor (nodo edge) diferente en cada caso.

4. Sin el header, el gateway usa `edge-us` por defecto:

   ```bash
   curl -s http://localhost:8080/
   ```

5. Apagar todo:

   ```bash
   docker compose down
   ```

## Notas

- `edge_node_hostname` en la salida es el hostname interno del contenedor
  Docker (no un valor a configurar); cambia en cada `docker compose up`.
- Las latencias en `simulated_network_latency_ms` son valores fijos de
  ejemplo (no miden red real) solo para ilustrar el concepto de "procesar
  cerca del usuario reduce la latencia" del post.
- En un entorno real, el rol de `X-Edge-Region` lo cumple la geolocalización
  automática de la CDN (ej. `CF-IPCountry` en Cloudflare Workers, como en el
  ejemplo del post); acá se pasa a mano por header para poder probar los
  tres nodos desde una sola máquina.
