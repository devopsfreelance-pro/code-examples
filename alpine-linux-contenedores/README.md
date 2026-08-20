# Alpine Linux for Containers

Post: https://www.devopsfreelance.pro/blog/en/posts/alpine-linux-docker-guide/

## What this example demonstrates

The post explains why Alpine Linux produces container images that are much
smaller than traditional distributions (Ubuntu, Debian), and shows a
multi-stage Python Dockerfile as the recommended pattern: a `builder` stage
with `gcc`/`musl-dev` that compiles the dependencies, and a final stage that
only copies the already-compiled artifacts, without leaving the compiler in
the production image.

This example reproduces that exact pattern with a minimal Flask app
(`app/app.py`, a `/health` endpoint) and compares it, side by side, against
the same code packaged the "traditional" way:

- `Dockerfile.alpine`: multi-stage build on `python:3.11-alpine`, matching
  the Dockerfile from the post (a `builder` stage with
  `gcc`/`musl-dev`/`python3-dev`, and a final stage with only the runtime
  and a non-root user created with `addgroup`/`adduser`).
- `Dockerfile.debian`: single-stage build on `python:3.11-slim`, leaving
  `gcc` installed in the final image, exactly what the post warns tends to
  happen when multi-stage isn't used.
- `scripts/compare_sizes.sh`: builds both images, prints the size
  difference with `docker images`, and runs a smoke test against `/health`
  on the Alpine image.

## Requirements

- Docker
- `curl` (used by the script for the smoke test)

## How to run it

```bash
cd alpine-linux-contenedores
./scripts/compare_sizes.sh
```

The script does, in order:

1. `docker build -f Dockerfile.alpine -t alpine-demo:alpine .`
2. `docker build -f Dockerfile.debian -t alpine-demo:debian .`
3. Prints a table comparing `alpine-demo:alpine` vs `alpine-demo:debian`
4. Starts `alpine-demo:alpine` on port 5000 and tests `/health`

## Expected output

A size table where the Alpine image is several times smaller than the
Debian slim one (exact values vary depending on the base image versions,
but the ratio holds, consistent with what the post describes). Actual
output from a test run:

```
TAG       SIZE
debian    315MB
alpine    59.5MB
```

And the final smoke test:

```
Respuesta de /health:
{"status":"ok"}
```

## Cleanup

```bash
docker rmi alpine-demo:alpine alpine-demo:debian
```

---

## 🇪🇸 Versión en español

# Alpine Linux para contenedores

Post: https://www.devopsfreelance.pro/blog/posts/alpine-linux-contenedores/

## Qué demuestra este ejemplo

El post explica por qué Alpine Linux produce imágenes de contenedor mucho
más chicas que distribuciones tradicionales (Ubuntu, Debian), y muestra un
Dockerfile multi-stage en Python como patrón recomendado: una etapa
`builder` con `gcc`/`musl-dev` que compila las dependencias, y una etapa
final que solo copia lo ya compilado, sin dejar el compilador en la imagen
de producción.

Este ejemplo reproduce exactamente ese patrón con una app Flask mínima
(`app/app.py`, un endpoint `/health`) y la compara, lado a lado, contra el
mismo código empaquetado de forma "tradicional":

- `Dockerfile.alpine`: multi-stage sobre `python:3.11-alpine`, igual al
  Dockerfile del post (etapa `builder` con `gcc`/`musl-dev`/`python3-dev`,
  etapa final solo con runtime y usuario no-root creado con
  `addgroup`/`adduser`).
- `Dockerfile.debian`: single-stage sobre `python:3.11-slim`, dejando
  `gcc` instalado en la imagen final, tal como advierte el post que suele
  pasar cuando no se usa multi-stage.
- `scripts/compare_sizes.sh`: construye ambas imágenes, imprime la
  diferencia de tamaño con `docker images`, y hace un smoke test contra
  `/health` en la imagen Alpine.

## Requisitos

- Docker
- `curl` (lo usa el script para el smoke test)

## Cómo correrlo

```bash
cd alpine-linux-contenedores
./scripts/compare_sizes.sh
```

El script hace, en orden:

1. `docker build -f Dockerfile.alpine -t alpine-demo:alpine .`
2. `docker build -f Dockerfile.debian -t alpine-demo:debian .`
3. Imprime una tabla comparando `alpine-demo:alpine` vs `alpine-demo:debian`
4. Levanta `alpine-demo:alpine` en el puerto 5000 y prueba `/health`

## Salida esperada

Una tabla de tamaños donde la imagen Alpine es varias veces más chica que
la Debian slim (los valores exactos varían según versión de las imágenes
base, pero la proporción se mantiene, en línea con lo que describe el
post). Salida real de una corrida de prueba:

```
TAG       SIZE
debian    315MB
alpine    59.5MB
```

Y el smoke test final:

```
Respuesta de /health:
{"status":"ok"}
```

## Limpieza

```bash
docker rmi alpine-demo:alpine alpine-demo:debian
```
