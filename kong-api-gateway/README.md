# Kong API Gateway: demo local con Docker Compose

Post del blog: [Kong API Gateway: Guía completa para arquitecturas modernas](https://www.devopsfreelance.pro/blog/posts/kong-api-gateway/)

## Qué demuestra este ejemplo

Un Kong API Gateway corriendo en **modo DB-less** (sin Postgres ni Cassandra,
configuración 100% declarativa vía YAML, tal como se recomienda en el post
para despliegues GitOps y Kubernetes) que hace de proxy hacia un backend de
prueba (`httpbin`). La configuración declarativa (`kong.yml`) define:

- Un **Service** y una **Route** (`/httpbin` -> `httpbin:80`).
- El plugin **rate-limiting**, limitando a 5 peticiones por minuto por
  servicio, con `policy: local` (sin dependencias externas).
- El plugin **request-transformer**, que añade un header (`X-Gateway`) a
  cada petición antes de reenviarla al backend, para ilustrar la
  transformación de peticiones en tránsito.

Con esto se ven en minutos, sin escribir código, los tres conceptos
centrales del post: proxy con Service/Route, rate limiting y transformación
mediante plugins.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- `curl`

No hace falta cuenta ni licencia: se usa la imagen oficial `kong:3.6` (Kong
Gateway OSS) y `kennethreitz/httpbin` como backend de prueba.

## Pasos para correrlo

1. Levantar Kong y el backend:

   ```bash
   docker compose up -d
   ```

2. Esperar unos segundos a que Kong arranque y confirmar que está sano:

   ```bash
   curl -s http://localhost:8001/status | head -c 200
   ```

3. Hacer una petición a través del gateway (Kong hace proxy hacia
   `httpbin`, quitando el prefijo `/httpbin` gracias a `strip_path: true`):

   ```bash
   curl -s http://localhost:8000/httpbin/headers
   ```

   En la respuesta JSON debe aparecer el header inyectado por el plugin
   `request-transformer`:

   ```json
   "X-Gateway": "Kong-Demo"
   ```

4. Probar el rate limiting con el script incluido (dispara 6 peticiones
   seguidas; el límite configurado es 5 por minuto):

   ```bash
   chmod +x test-rate-limit.sh
   ./test-rate-limit.sh
   ```

   Salida esperada:

   ```
   Peticion 1 -> HTTP 200
   Peticion 2 -> HTTP 200
   Peticion 3 -> HTTP 200
   Peticion 4 -> HTTP 200
   Peticion 5 -> HTTP 200
   Peticion 6 -> HTTP 429
   ```

5. (Opcional) Ver los headers de rate limiting que Kong agrega a cada
   respuesta (`X-RateLimit-Remaining-Minute`, etc.):

   ```bash
   curl -s -D - -o /dev/null http://localhost:8000/httpbin/get
   ```

6. Apagar todo:

   ```bash
   docker compose down
   ```

## Archivos

- `docker-compose.yml`: levanta Kong (modo DB-less) y el backend `httpbin`.
- `kong.yml`: configuración declarativa de Kong (Service, Route y plugins).
- `test-rate-limit.sh`: script que verifica el comportamiento del plugin
  rate-limiting.

## Notas

- El puerto `8001` (Admin API) queda expuesto solo para uso local de esta
  demo; en producción no debe exponerse sin autenticación/red restringida.
- Esperar 1 minuto entre corridas de `test-rate-limit.sh` para que la
  ventana de rate limiting se reinicie, o reiniciar el contenedor de Kong
  (`docker compose restart kong`).
