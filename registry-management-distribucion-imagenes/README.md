# Docker Registry: gestion y distribucion de imagenes

Ejemplo ejecutable que acompaña al post [Docker Registry: Guía completa de gestión y distribución](https://www.devopsfreelance.pro/blog/posts/registry-management-distribucion-imagenes/).

## Que demuestra

Un docker registry local (imagen oficial `registry:2`, la implementacion de referencia de la especificacion OCI de distribucion) donde se puede ver en la practica lo que el post explica de forma conceptual:

- Como funciona el flujo push/pull contra un registry propio en vez de Docker Hub.
- Versionado semantico explicito (`v1.0.0`) en lugar de `latest`.
- Inspeccion del catalogo de repositorios, los tags y el manifiesto de una imagen usando la API HTTP de distribucion (`/v2/...`), la misma que usa `docker` internamente.
- Como un consumidor descarga (`pull`) capas que ya no tiene localmente.
- Garbage collection: borrar un manifiesto por digest y compactar las capas huerfanas que quedan sin referencias, tal como se describe en la seccion de mantenimiento del post.
- Un ejemplo comentado de configuracion `proxy.remoteurl` para convertir el registry en un pull-through cache de Docker Hub (patron mencionado para reducir egress y latencia).

No implementa Harbor completo (RBAC, escaneo de vulnerabilidades, replicacion) porque eso requiere una instalacion mucho mas pesada; el objetivo es que se entienda el mecanismo subyacente de cualquier OCI registry, que es lo que Harbor envuelve con features empresariales.

## Requisitos

- Docker Engine con el plugin `docker compose` (Docker Desktop o Docker CE 20.10+).
- `curl`.
- Puerto `5000` libre en localhost.

## Como correrlo

```bash
cd registry-management-distribucion-imagenes
./demo.sh
```

El script:

1. Levanta el registry local con `docker compose up -d`.
2. Construye una imagen minima de ejemplo (`alpine` + un archivo de texto).
3. La etiqueta como `localhost:5000/demo-app:v1.0.0`.
4. Hace `docker push` al registry local.
5. Consulta el catalogo de repositorios (`GET /v2/_catalog`).
6. Lista los tags del repositorio (`GET /v2/demo-app/tags/list`).
7. Obtiene el manifiesto de la imagen (`GET /v2/demo-app/manifests/v1.0.0`).
8. Borra la imagen local y la vuelve a bajar (`docker pull`) para simular otro consumidor.
9. Borra el manifiesto por digest (`DELETE /v2/demo-app/manifests/<digest>`) y corre `garbage-collect` dentro del contenedor del registry.

Para apagar todo y borrar el volumen de datos:

```bash
docker compose down -v
```

## Salida esperada (resumen)

```
=== 1. Levantar el registry local ===
Registry OK en http://localhost:5000/v2/

=== 4. Push al registry local ===
The push refers to repository [localhost:5000/demo-app]
...
v1.0.0: digest: sha256:... size: ...

=== 5. Listar el catalogo de repositorios via API de distribucion ===
{"repositories":["demo-app"]}

=== 6. Listar tags del repositorio ===
{"name":"demo-app","tags":["v1.0.0"]}

=== 7. Obtener el manifiesto ===
{"schemaVersion":2,"mediaType":"application/vnd.docker.distribution.manifest.v2+json", ...}

=== 8. Simular un consumidor ===
v1.0.0: Pulling from demo-app
...
imagen de demo para registry management

=== 9. Garbage collection ===
Digest del manifiesto: sha256:...
DELETE manifest -> HTTP 202
...blobs eliminated, ... bytes freed...

Demo completa. Para apagar el registry: docker compose down -v
```

## Archivos

- `docker-compose.yml`: levanta el registry (`registry:2`) con un volumen persistente y la config custom.
- `config.yml`: configuracion minima del registry (storage, delete habilitado, healthcheck) mas el ejemplo comentado de pull-through cache.
- `demo.sh`: automatiza todo el flujo push/pull/inspeccion/garbage-collection descripto arriba.

No hay secretos ni cuentas externas involucradas: todo corre en localhost.
