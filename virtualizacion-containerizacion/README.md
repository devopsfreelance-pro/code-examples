# Virtualización Linux: Docker vs Podman, cgroups en la práctica

Post: [Virtualización Linux: Guía Completa KVM, LXC y Contenedor](https://www.devopsfreelance.pro/blog/posts/virtualizacion-containerizacion/)

## Qué demuestra este ejemplo

El post explica que un contenedor no es una máquina virtual: es un proceso Linux
aislado con namespaces y limitado con cgroups, corriendo sobre el mismo kernel
del host, y que Docker y Podman son intercambiables porque Podman mantiene
compatibilidad de CLI con Docker sin usar un daemon central.

Este mini ejemplo lo hace tangible:

- Una imagen mínima con un servidor HTTP en Python que lee sus propios límites
  de CPU y memoria directamente desde `/sys/fs/cgroup/`, es decir, muestra
  desde adentro del contenedor lo que el runtime le impuso al kernel.
- Un `docker-compose.yml` que arranca ese contenedor con límites de CPU
  (`0.5` core) y memoria (`128m`), igual que se describe en la sección de
  cgroups del post.
- Un script (`compare-docker-podman.sh`) que construye y corre el mismo
  contenedor primero con Docker y, si está instalado, después con Podman,
  usando comandos casi idénticos, y además muestra el PID del contenedor
  visto desde el host (evidencia de que es un proceso más, no una VM).

No incluye una demo de KVM ni LXC porque requieren virtualización anidada o
privilegios de host que no son razonables para correr en minutos en cualquier
máquina; el foco del ejemplo es la parte de containerización, que es la que
se puede ejecutar de punta a punta sin infraestructura adicional.

## Requisitos

- Docker Engine (con `docker compose` o el plugin `docker-compose`)
- Opcional: Podman, para ver la comparación de la sección 5 del script
- `curl` (para probar el endpoint)

No se necesita ninguna cuenta ni credencial: todo corre en local.

## Cómo correrlo

### Opción A: con docker-compose

```bash
cd virtualizacion-containerizacion
docker compose up --build -d
curl http://localhost:8080/
docker compose down
```

Salida esperada de `curl`:

```json
{
  "hostname": "a1b2c3d4e5f6",
  "pid_dentro_del_contenedor": 1,
  "cgroup_cpu_limit_path": "/sys/fs/cgroup/cpu.max",
  "cgroup_cpu_limit_value": "50000 100000",
  "cgroup_mem_limit_path": "/sys/fs/cgroup/memory.max",
  "cgroup_mem_limit_value": "134217728"
}
```

(`50000 100000` significa 0.5 CPU; `134217728` bytes son los 128MB configurados.
Los valores exactos y las rutas de cgroup pueden variar según la versión del
kernel host: v1 usa `cpu.cfs_quota_us` / `memory.limit_in_bytes`, v2 usa
`cpu.max` / `memory.max`.)

### Opción B: script comparando Docker y Podman

```bash
cd virtualizacion-containerizacion
chmod +x compare-docker-podman.sh
./compare-docker-podman.sh
```

El script:

1. Construye la imagen con Docker.
2. Corre el contenedor con límites de CPU/memoria y consulta el endpoint.
3. Muestra el PID del contenedor tal como lo ve el proceso `dockerd` en el
   host (namespaces, no un hipervisor).
4. Si Podman está instalado, repite los pasos 1-2 con Podman para mostrar
   que la CLI es prácticamente la misma.

Salida esperada (resumida):

```
== 1) Build de la imagen con Docker ==
...
== 3) Info del proceso/cgroup visto desde dentro del contenedor ==
{
  "hostname": "...",
  ...
}

== 4) Proceso del contenedor visible en el host (namespaces, no VM) ==
PID en el host: 12345

== 5) Mismo flujo con Podman (sin daemon, rootless) ==
...
```

## Limpieza

```bash
docker compose down --rmi local
# o, si usaste el script:
docker rm -f virtualizacion-demo-cli 2>/dev/null
podman rm -f virtualizacion-demo-cli 2>/dev/null
```
