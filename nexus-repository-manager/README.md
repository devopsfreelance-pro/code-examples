# Nexus Repository Manager: proxy, hosted y group en acción

Ejemplo de código para el post [Nexus Repository: Guía completa para gestión de artefactos](https://www.devopsfreelance.pro/blog/posts/nexus-repository-manager/).

## Qué demuestra

El post explica que la potencia de Nexus está en combinar sus tres tipos de
repositorio (proxy, hosted y group). Este ejemplo levanta una instancia real
de Nexus Repository OSS con Docker y, con un único script, reproduce los tres
conceptos contra el servidor:

1. **Repositorio proxy** (`maven-central`, viene creado por defecto): se
   descarga la misma dependencia Maven (`commons-lang3`) dos veces y se mide
   el tiempo de cada descarga. La primera va a buscar el artefacto a Maven
   Central; la segunda se sirve desde la caché local de Nexus y es
   sensiblemente más rápida, tal como describe el post en la sección de
   repositorios proxy.
2. **Repositorio hosted** (`internal-artifacts`, se crea con la API REST):
   se publica un artefacto propio con `PUT` y se lo recupera con `GET`,
   igual que publicarías una biblioteca interna generada por tu propio
   pipeline.
3. **Repositorio group** (`todo-en-uno`, se crea con la API REST): agrupa el
   repositorio hosted detrás de una única URL, mostrando la abstracción que
   el post menciona para simplificar la configuración de las herramientas de
   build.

Al final el script lista todos los repositorios de la instancia (tipo,
formato y nombre) usando la API REST de Nexus (`/service/rest/v1/repositories`).

## Requisitos

- Docker y Docker Compose
- `curl`
- Python 3 (solo para formatear el listado final de repositorios, viene
  preinstalado en la mayoría de sistemas)
- ~2 GB de RAM libres para el contenedor de Nexus (arranca en 1-2 minutos)
- Puerto `8081` libre en localhost

No se usa Nexus Pro ni ningún servicio pago: todo corre con la imagen oficial
`sonatype/nexus3` (edición OSS) en un contenedor local.

## Pasos para ejecutarlo

### 1. Levantar Nexus

```bash
docker compose up -d
```

### 2. Correr la demo

El script espera a que Nexus esté listo, obtiene la password inicial de
admin generada automáticamente por el contenedor, y ejecuta los tres
escenarios (proxy, hosted, group):

```bash
chmod +x demo.sh
./demo.sh
```

La primera vez puede tardar 1-2 minutos en el paso de espera, mientras Nexus
termina de arrancar dentro del contenedor.

### 3. Apagar todo

```bash
docker compose down -v
```

El flag `-v` borra también el volumen `nexus-data`, para que la próxima vez
arranque desde cero con una password de admin nueva.

## Salida esperada

```
==> 1) Esperando a que Nexus responda en http://localhost:8081 ...
....
Nexus está arriba.
==> 2) Obteniendo password inicial de admin ...
Password inicial obtenida (se usa solo para esta demo local).

==> 3) Repositorio PROXY: maven-central ya viene creado por defecto en Nexus OSS.
    Descargamos la misma dependencia dos veces a través del proxy y medimos el tiempo.
    La primera vez Nexus la baja de Maven Central; la segunda la sirve desde su caché local.

--- Descarga 1 (origen remoto) ---
Tiempo: 850 ms | tamaño: 658734 bytes

--- Descarga 2 (desde caché de Nexus) ---
Tiempo: 40 ms | tamaño: 658734 bytes

La descarga cacheada (2) debería ser notablemente más rápida que la original (1).

==> 4) Repositorio HOSTED: creamos uno raw para artefactos propios y publicamos uno.
--- Publicando /tmp/mi-artefacto.txt en el repo hosted ---
--- Descargando de vuelta el mismo artefacto ---
hola desde devopsfreelance.pro - 2026-08-20T12:00:00Z

==> 5) Repositorio GROUP: unificamos el proxy y el hosted bajo una sola URL.
--- Listando repositorios existentes en esta instancia ---
  proxy    maven  maven-central
  hosted   maven  maven-releases
  hosted   maven  maven-snapshots
  group    maven  maven-public
  hosted   nuget  nuget-hosted
  proxy    nuget  nuget.org-proxy
  group    nuget  nuget-group
  hosted   raw    internal-artifacts
  group    raw    todo-en-uno

Demo completa. UI disponible en http://localhost:8081 (usuario admin, password: <password-generada>)
```

Los tiempos exactos van a variar según tu conexión y tu máquina, pero la
descarga 2 (cacheada) siempre debería ser un orden de magnitud más rápida
que la descarga 1. La password de admin que aparece en la salida es la
generada automáticamente por el contenedor en cada arranque (no hay ningún
secreto hardcodeado en el repo): se guarda en `/nexus-data/admin.password`
dentro del contenedor y se borra tras el primer login desde la UI.

## Ir más allá

Podés abrir `http://localhost:8081` en el navegador (usuario `admin`,
password la que imprime el script) para ver visualmente los repositorios
creados y navegar el contenido cacheado de `maven-central` en
**Browse > maven-central**.
