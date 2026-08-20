# Diagnostico de problemas de rendimiento

Ejemplo ejecutable del post [Diagnostico de problemas de rendimiento](https://www.devopsfreelance.pro/blog/posts/diagnostico-problemas-rendimiento/).

## Que demuestra

El post explica el flujo de diagnostico de un cuello de botella: medir sintomas,
identificar la causa raiz y aplicar una solucion (caching, en el ejemplo de
Python + Redis del articulo). Este ejemplo reproduce ese flujo completo con
una app real:

- **app/server.py**: una app HTTP minima (sin frameworks) con dos endpoints
  que ejecutan la misma "operacion costosa" simulada (~300ms):
  - `/slow`: siempre paga el costo completo (representa el sintoma: tiempos
    de respuesta lentos por falta de caching).
  - `/slow-cached`: usa el mismo decorador `cache()` con Redis que aparece
    en el post; la primera llamada paga el costo, las siguientes (dentro de
    la ventana de expiracion) responden en pocos milisegundos.
- **benchmark.sh**: hace varias requests contra ambos endpoints y muestra el
  tiempo de respuesta de cada una, dejando en evidencia el "antes" (`/slow`)
  y el "despues" (`/slow-cached`) del diagnostico.
- **alert-rules.yml**: la regla de alerta de Prometheus del post
  (`HighCPUUsage`), incluida como referencia para cuando el diagnostico
  apunta a saturacion de CPU en vez de falta de caching. No se ejecuta en
  este stack (ver seccion "Fuera de alcance" mas abajo).

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- `curl` y `python3` (para correr `benchmark.sh`; ya vienen en la mayoria de distros)

No requiere cuentas ni servicios pagos: todo corre local en contenedores.

## Pasos para correrlo

1. Levantar el stack (app + Redis):

```bash
cd diagnostico-problemas-rendimiento
docker compose up -d --build
```

2. Esperar unos segundos a que la app este arriba y verificarlo:

```bash
curl http://localhost:8090/health
# {"status": "ok", "elapsed_ms": 0.0}
```

3. Correr el benchmark de diagnostico:

```bash
chmod +x benchmark.sh
./benchmark.sh
```

4. Cuando termines, apagar el stack:

```bash
docker compose down
```

## Salida esperada

En `/slow`, las 5 requests deberian tardar todas ~300ms (el cuello de
botella no tiene mitigacion):

```
== Diagnostico: endpoint SIN cache (/slow) ==
  request 1: 301.2 ms
  request 2: 300.8 ms
  request 3: 301.5 ms
  request 4: 300.6 ms
  request 5: 301.1 ms
```

En `/slow-cached`, solo la primera request paga el costo completo; el resto
responde desde Redis en pocos milisegundos:

```
== Solucion: endpoint CON cache en Redis (/slow-cached) ==
  request 1: 301.4 ms
  request 2: 2.1 ms
  request 3: 1.8 ms
  request 4: 1.9 ms
  request 5: 2.0 ms
```

Esa diferencia (300ms vs pocos ms) es la confirmacion, con numeros, de que
la causa raiz del sintoma inicial era la falta de caching y de que la
solucion aplicada la resuelve.

## Fuera de alcance

El post tambien menciona Prometheus + Grafana para monitoreo de CPU/memoria
(`alert-rules.yml` incluido como referencia). Ese stack completo de
observabilidad ya esta cubierto en detalle en el ejemplo del post
[Monitoreo con Prometheus y Grafana](../monitoreo-con-prometheus-grafana/),
por eso aca no se duplica.
