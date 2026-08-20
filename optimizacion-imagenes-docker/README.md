# Optimizacion de imagenes Docker con multi-stage builds

Post relacionado: [Optimizar Docker: Estrategias para imagenes eficientes](https://www.devopsfreelance.pro/blog/posts/optimizacion-imagenes-docker/)

## Que demuestra este ejemplo

El post explica que la tecnica mas efectiva para reducir el tamano de una
imagen Docker es separar el entorno de construccion del entorno de ejecucion
mediante **multi-stage builds**. Este ejemplo compila la misma aplicacion Go
de dos formas distintas para que se vea la diferencia de forma concreta:

- `Dockerfile.sin-optimizar`: una sola etapa basada en `golang:1.21` (imagen
  completa con compilador, herramientas de build y todo el toolchain de Go
  incluido en la imagen final).
- `Dockerfile.optimizado`: multi-stage build de dos etapas. La primera
  compila un binario estatico (`CGO_ENABLED=0`) sobre `golang:1.21-alpine`;
  la segunda copia unicamente ese binario a una imagen `scratch` (vacia).

El script `compare-sizes.sh` construye ambas imagenes y muestra la diferencia
de tamano lado a lado, ademas de levantar un contenedor con la version
optimizada para confirmar que responde correctamente.

## Requisitos

- Docker (Engine o Desktop) instalado y corriendo.
- `curl` disponible en el host (usado solo para el healthcheck del script).
- No requiere cuentas ni credenciales de ningun servicio externo.

## Como correrlo

```bash
cd optimizacion-imagenes-docker
./compare-sizes.sh
```

Si preferis construir las imagenes manualmente:

```bash
# Version sin optimizar
docker build -f Dockerfile.sin-optimizar -t docker-size-demo:sin-optimizar .

# Version optimizada (multi-stage)
docker build -f Dockerfile.optimizado -t docker-size-demo:optimizado .

# Comparar tamanos
docker images | grep docker-size-demo
```

Para probar la imagen optimizada manualmente:

```bash
docker run -d -p 8080:8080 --name demo docker-size-demo:optimizado
curl http://localhost:8080/
docker stop demo && docker rm demo
```

## Salida esperada

El script imprime una tabla con ambas imagenes y sus tamanos. La diferencia
es dramatica porque `golang:1.21` sola pesa varios cientos de MB (compilador
+ herramientas), mientras que `scratch` con el binario estatico agregado pesa
apenas unos pocos MB:

```
==> Comparacion de tamanos:
REPOSITORY:TAG                    SIZE
docker-size-demo:optimizado       6.72MB
docker-size-demo:sin-optimizar    884MB

==> Probando que la imagen optimizada funciona:
OK - servicio de ejemplo para optimizacion de imagenes Docker

==> Listo. La imagen optimizada deberia pesar unos pocos MB vs cientos de MB de la version sin optimizar.
```

Los tamanos exactos varian segun la version de Go y la arquitectura del host,
pero la proporcion (decenas o cientos de veces mas chica) se mantiene y es el
punto central que ilustra el post: separar build-time de runtime con
multi-stage builds elimina de la imagen final todo lo que no se necesita para
ejecutar la aplicacion.
