# Serverless vs. Contenedores: benchmark del modelo de ejecución

Post: [Serverless vs. Contenedores: Guía Comparativa para DevOps 2025](https://www.devopsfreelance.pro/blog/posts/serverless-vs-contenedores-guia-comparativa/)

## Qué demuestra este ejemplo

El post compara serverless y contenedores en varios ejes (costos, escalabilidad,
operaciones). El punto más concreto y medible de esa comparación es el **modelo
de ejecución**: un contenedor mantiene un proceso persistente ("warm") que
atiende múltiples requests reutilizando el mismo intérprete, mientras que una
función serverless típicamente arranca un entorno de ejecución nuevo por
invocación cuando no hay una instancia caliente disponible (cold start).

Este ejemplo reproduce ambos modelos localmente, sin nube, y mide la
diferencia real de latencia:

- **`app.py` + `Dockerfile` + `docker-compose.yml`**: un servidor HTTP simple
  (sin frameworks externos, solo `http.server` de la librería estándar) que
  representa el modelo *contenedor*: se levanta una vez y responde N requests
  con el mismo proceso.
- **`serverless_sim.py`**: representa el modelo *serverless*. Cada invocación
  se ejecuta como un proceso Python nuevo (`python3 serverless_sim.py <texto>`),
  procesa el "evento" y termina, igual que ocurriría con un cold start de
  AWS Lambda.
- **`benchmark.py`**: ejecuta N invocaciones contra el contenedor (vía HTTP) y
  N invocaciones del script serverless (vía subprocess), mide la latencia de
  cada una y compara los promedios.

Ambos scripts comparten la misma lógica de negocio (contar palabras, caracteres
y devolver el texto invertido) para que la comparación de latencia sea
"manzanas con manzanas": la única variable es el modelo de ejecución, no el
código que corre.

## Requisitos

- Docker + Docker Compose (`docker compose version`)
- Python 3.9+ (sin dependencias externas, todo con librería estándar)

## Pasos para correrlo

```bash
# 1. Levantar el "contenedor" (proceso persistente)
docker compose up -d --build

# 2. Verificar que responde
curl "http://localhost:8000/process?text=hola+mundo"
# {"words": 2, "chars": 10, "reversed": "odnum aloh"}

# 3. Probar el "serverless" simulado por separado (opcional)
python3 serverless_sim.py "hola mundo"
# {"statusCode": 200, "body": {"words": 2, "chars": 10, "reversed": "odnum aloh"}}

# 4. Correr el benchmark comparativo (por defecto 20 invocaciones por modelo)
python3 benchmark.py 20

# 5. Apagar el contenedor
docker compose down
```

## Salida esperada

El benchmark imprime algo similar a esto (los valores exactos varían según la
máquina, pero la relación se mantiene):

```
Ejecutando benchmark con 20 invocaciones por modelo...

Contenedor (proceso persistente, warm):
  invocaciones : 20
  promedio     : 1.28 ms
  min / max    : 0.57 ms / 9.51 ms

Serverless simulado (proceso nuevo por invocación):
  invocaciones : 20
  promedio     : 20.23 ms
  min / max    : 19.05 ms / 22.16 ms

El modelo serverless simulado fue en promedio 15.8x más lento por invocación
debido al costo de arrancar un proceso nuevo cada vez (análogo al cold start
de Lambda).
```

## Qué NO demuestra este ejemplo

Esto es una simulación local del *modelo* de ejecución, no un benchmark de
AWS Lambda real: no incluye la latencia de red hacia un proveedor cloud, ni el
tiempo de inicialización de un runtime administrado (que puede ser mayor o
menor según el lenguaje y el tamaño del paquete). El objetivo es ilustrar de
forma reproducible y sin costo por qué el post afirma que serverless tiene
overhead de cold start y contenedores no, no reemplazar una prueba de carga
contra infraestructura real.

## Sin cuentas ni secretos

Este ejemplo no requiere cuenta de AWS, Docker Hub ni ningún servicio pago:
todo corre en `localhost`.
