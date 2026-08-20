# Envoy Proxy: routing dinámico y canary con weighted clusters

Post: [Envoy Proxy y Service Mesh: Guía Completa para DevOps](https://www.devopsfreelance.pro/blog/posts/envoy-proxy-service-mesh/)

## Qué demuestra

El post explica que Envoy separa la lógica de red (routing, timeouts, retries, balanceo)
de la aplicación, y que un service mesh como Istio usa esa capacidad para hacer canary
releases por peso sin tocar código (el ejemplo de `VirtualService` 90/10 del post).

Este mini-laboratorio reproduce esa misma idea con Envoy standalone (sin Kubernetes ni
Istio, para poder correrlo en cualquier máquina con Docker):

- Un Envoy escuchando en `:10000` con configuración **estática** (`envoy.yaml`), igual en
  estructura al ejemplo del post: `listener` → `http_connection_manager` → `route` → `clusters`.
- Dos backends (`pagos-v1` y `pagos-v2`) simulados con contenedores livianos.
- Un `route` con **`weighted_clusters`**: 90% del tráfico va a `pagos-v1` y 10% a
  `pagos-v2`, la versión Envoy "pura" del `VirtualService` de Istio que aparece en el post.
- `timeout: 3s` y `retry_policy` con `retry_on: 5xx` y `num_retries: 2`, igual que el
  primer bloque de configuración del post.
- La `admin interface` de Envoy en `:9901`, para inspeccionar clusters y stats como se
  describe en la sección de debugging del post (`config_dump`, `clusters`, etc.).

No incluye Istio ni Kubernetes: eso está cubierto en la guía de
[service mesh con Istio](https://www.devopsfreelance.pro/blog/posts/service-mesh-con-istio/)
enlazada al final del post. Acá el foco es entender Envoy en sí mismo, que es el
prerequisito que el post recomienda dominar primero.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- `curl` (para probar y para el script de verificación)
- Puertos libres en el host: `10000` y `9901`

## Pasos para correrlo

1. Levantar Envoy y los dos backends:

```bash
docker compose up -d
```

2. Confirmar que los tres contenedores están corriendo:

```bash
docker compose ps
```

3. Hacer una request de prueba (puede caer en v1 o v2):

```bash
curl http://localhost:10000/
```

Salida esperada (una de las dos, según el balanceo):

```
respuesta de pagos v1
```
o
```
respuesta de pagos v2
```

4. Verificar el split de tráfico 90/10 enviando varias requests:

```bash
./test-canary-split.sh 50
```

Salida esperada (aproximada, el split es probabilístico):

```
Enviando 50 requests a http://localhost:10000/ ...

Resultado del split de tráfico:
  pagos-v1: 45 requests
  pagos-v2: 5 requests

Esperado (aprox, weighted_clusters 90/10): v1 ~90%, v2 ~10%
```

5. Inspeccionar el estado real de los clusters vía la admin interface de Envoy (lo que
   en el post se hace con `istioctl proxy-config` sobre un sidecar real):

```bash
curl -s http://localhost:9901/clusters | grep -E "pagos_v1|pagos_v2"
```

Debe mostrar ambos clusters con sus endpoints en estado `health_flags::healthy`.

6. Ver la configuración completa que Envoy tiene cargada (equivalente estático al
   `config_dump` que el post usa para debugging en un mesh real):

```bash
curl -s http://localhost:9901/config_dump | head -50
```

7. Apagar todo:

```bash
docker compose down
```

## Archivos

- `docker-compose.yml`: levanta Envoy + dos backends (`hashicorp/http-echo`).
- `envoy.yaml`: configuración estática de Envoy (listener, route con `weighted_clusters`,
  retries, timeout, y los dos clusters de destino).
- `test-canary-split.sh`: envía N requests y cuenta cuántas cayeron en cada versión, para
  verificar el split de tráfico ponderado.

## Notas

- Las imágenes usadas (`envoyproxy/envoy`, `hashicorp/http-echo`) son públicas y gratuitas,
  no requieren cuenta ni credenciales.
- Para pasar de este laboratorio al `VirtualService` de Istio del post, la traducción
  conceptual es directa: `weighted_clusters` en Envoy es lo que Istio genera automáticamente
  a partir de un `VirtualService` con `weight: 90` / `weight: 10`, y se lo empuja a cada
  sidecar vía xDS en vez de un archivo estático como `envoy.yaml`.
