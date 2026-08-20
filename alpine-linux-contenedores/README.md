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
