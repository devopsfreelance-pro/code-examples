# Chaos Engineering: mini-experimento con Toxiproxy

Post: [Chaos Engineering: Fortaleciendo la Resiliencia de Sistemas Distribuidos](https://www.devopsfreelance.pro/blog/posts/chaos-engineering--fortaleciendo-la-resiliencia-de-sistemas-distribuidos/)

## Qué demuestra

Este ejemplo reproduce en miniatura el ciclo completo de un experimento de
Chaos Engineering descripto en el post (los cuatro pilares y el flujo de
Chaos Toolkit / Toxiproxy):

1. **Hipótesis de estado estable**: se mide la latencia base de un
   `payment-service` de juguete y se confirma que responde por debajo de un
   umbral aceptable.
2. **Inyección de fallo real**: se agrega una toxina de latencia de red
   (1000 ms ± 50 ms de jitter) al tráfico hacia el servicio usando
   [Toxiproxy](https://github.com/Shopify/toxiproxy), la misma herramienta
   que se muestra en la sección "Capa de Red" del post.
3. **Observación**: se vuelve a medir la latencia mientras el fallo está
   activo, mostrando la degradación real del sistema.
4. **Rollback y verificación**: se elimina la toxina automáticamente y se
   confirma que el sistema recuperó su estado estable, tal como indica el
   plan de mitigación (`automatic_revert`) descripto en el post.

El servicio "payment-service" es un servidor HTTP mínimo en Python (sin
dependencias) que expone `GET /health`. Toxiproxy se sienta como proxy TCP
delante de él, así el experimento inyecta el fallo a nivel de red sin tocar
el código de la aplicación, igual que en un escenario real.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- `curl` (para el script del experimento)
- Puertos libres en el host: `8080` (proxy) y `8474` (API de Toxiproxy)

## Estructura

```
chaos-engineering--fortaleciendo-la-resiliencia-de-sistemas-distribuidos/
├── docker-compose.yml     # servicio "api" + Toxiproxy
├── toxiproxy.json         # define el proxy payment_service (8080 -> api:5000)
├── api/app.py             # servidor HTTP mínimo (GET /health)
└── chaos_experiment.sh    # script del experimento de caos
```

## Pasos para correrlo

1. Levantar el stack (API + Toxiproxy):

   ```bash
   docker compose up -d
   ```

2. Confirmar que el proxy responde directamente (sin fallo inyectado):

   ```bash
   curl http://localhost:8080/health
   # {"status": "ok", "service": "payment-service"}
   ```

3. Ejecutar el experimento de caos:

   ```bash
   chmod +x chaos_experiment.sh
   ./chaos_experiment.sh
   ```

4. Limpiar el entorno al terminar:

   ```bash
   docker compose down
   ```

## Salida esperada

```
=== 1. Hipotesis de estado estable ===
Hipotesis: /health responde en menos de 300ms
Latencia medida (baseline): 4ms
OK: estado estable confirmado.

=== 2. Inyeccion de fallo: latencia de red de 1000ms ===
Toxic 'latency_down' agregada al proxy payment_service.

=== 3. Observacion durante el fallo ===
Latencia medida (con fallo inyectado): 1027ms

=== 4. Rollback: eliminar la toxina ===
Toxic eliminada.

=== 5. Verificacion de recuperacion ===
Latencia medida (post-rollback): 5ms
OK: el sistema recupero su estado estable.

=== Resultado del experimento ===
Baseline:   4ms
Con fallo:  1027ms (aumento de 1023ms)
Recuperado: 5ms
```

Los valores exactos de latencia van a variar según la máquina, pero el
patrón (baseline bajo -> degradación tras la toxina -> recuperación tras el
rollback) es el resultado esperado.

## Ir más allá

- Cambiar `LATENCY_MS` en `chaos_experiment.sh` o agregar otras toxinas
  (`bandwidth`, `timeout`, `slow_close`) vía la API de Toxiproxy
  (`http://localhost:8474`) para simular otros escenarios del post.
- Este ejemplo usa Toxiproxy porque corre 100% local sin cuenta ni licencia.
  Las herramientas nativas de Kubernetes mencionadas en el post (Chaos Mesh,
  Litmus Chaos) requieren un clúster (por ejemplo `kind`) y quedan fuera del
  alcance de este mini-ejemplo.
