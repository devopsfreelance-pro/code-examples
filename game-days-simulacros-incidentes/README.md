# Game Days y Simulacros de Incidentes

Ejemplo de código para el post [Guía Completa de Game days y simulacros de incidentes](https://www.devopsfreelance.pro/blog/posts/game-days-simulacros-incidentes/).

## Qué demuestra este ejemplo

Un mini game day ejecutable localmente sobre un servicio de pagos de juguete:

1. Un servicio Flask (`payment-service`) instrumentado con `prometheus_client`, siguiendo
   el mismo patrón de métricas (`game_day_requests_total`, `game_day_request_duration_seconds`)
   que se muestra en el post.
2. Prometheus scrapeando ese servicio, tal como recomienda la sección de observabilidad
   del post.
3. Un script (`scripts/run_game_day.sh`) que reproduce las fases descritas en el ejemplo
   de escenario del post ("Degradación de Servicio de Pagos"):
   - Fase 1: línea base con el sistema sano.
   - Fase 2: inyección del fallo (la "dependencia externa" empieza a responder con
     latencia alta y timeouts, simulando lo que Chaos Mesh/Pumba harían a nivel de red).
   - Fase 3: verificación de que la métrica de errores en Prometheus detecta la
     degradación.
   - Fase 4: reversión del fallo y confirmación de la recuperación.

No se usa Chaos Mesh (requiere un cluster Kubernetes) ni Pumba (requiere montar el socket
de Docker) para mantener el ejemplo corriendo en minutos con un solo `docker compose up`.
La inyección de fallo se simula a nivel de aplicación vía el endpoint `/toggle-dependency`,
que es el mismo concepto que un "facilitador" de game day activaría con las herramientas
reales del post.

## Requisitos

- Docker y Docker Compose (plugin `docker compose`, no el binario viejo `docker-compose`).
- `curl` y `python3` (ya suelen venir instalados en Linux/macOS).
- Puertos libres en `localhost`: `8000` (servicio) y `9090` (Prometheus).

No hace falta ninguna cuenta ni credencial externa.

## Cómo correrlo

1. Levantar el stack (build de la imagen del servicio + Prometheus):

   ```bash
   docker compose up -d --build
   ```

2. Esperar a que el servicio esté sano (unos segundos):

   ```bash
   docker compose ps
   ```

   Deberías ver `game-day-payment-service` en estado `healthy`.

3. Correr el simulacro:

   ```bash
   chmod +x scripts/run_game_day.sh
   ./scripts/run_game_day.sh
   ```

4. (Opcional) explorar las métricas crudas o en Prometheus:

   ```bash
   curl -s http://localhost:8000/metrics | grep game_day
   ```

   O abrir `http://localhost:9090/graph` y consultar `game_day_requests_total`.

5. Terminar el ejercicio y limpiar:

   ```bash
   docker compose down
   ```

## Salida esperada

El script imprime las cuatro fases con el resultado de cada request. En la fase de
"incidente" vas a ver latencias entre 2 y 4 segundos y varios `status=504` (el 40% de
las requests fallan por timeout, tal como configura `call_external_payment_provider()`
en `app/app.py`). En "baseline" y "recuperacion" las latencias deberían ser menores a
0.1s y sin errores. El resumen final se ve así (los números exactos varían por la
aleatoriedad del simulacro):

```
=== Resumen del game day ===
Errores baseline:    0/20
Errores en incidente: 7/20
Errores post-recuperación: 0/20
Resultado: el sistema detectó y se recuperó del fallo inyectado. Objetivo del game day cumplido.
```

## Ir más allá

- Cambiar `random.uniform(2.0, 4.0)` y la probabilidad `0.4` en `app/app.py` para simular
  escenarios más o menos severos (como las fases del ejemplo del post).
- Sumar un segundo servicio dependiente para ver cascadas de fallos, otro concepto
  central del post.
- Reemplazar la inyección simulada por Pumba real: `docker run --rm -v /var/run/docker.sock:/var/run/docker.sock gaiaadm/pumba pumba netem --duration 30s delay --time 300 game-day-payment-service` (requiere dar acceso al socket de Docker, por eso queda fuera del ejemplo por defecto).
