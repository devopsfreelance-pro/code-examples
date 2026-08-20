# Cgroups and namespaces in practice

Runnable example for the post [Advanced Linux System Administration: Master Enterprise Linux](https://www.devopsfreelance.pro/blog/en/posts/advanced-linux-system-administration/).

## What it demonstrates

The post explains cgroups and namespaces by creating cgroups by hand with `mkdir` in
`/sys/fs/cgroup/`. This example shows that Docker is nothing more than an
automation layer on top of those same kernel mechanisms, and proves it in
practice:

1. Builds an image with `stress-ng` that tries to reserve 150 MB of RAM.
2. Runs it in a container with a memory limit of 100 MB
   (`--memory=100m`), i.e. a real cgroup created by Docker.
3. Confirms in the log that the kernel kills the process repeatedly for
   exceeding the limit (OOM-kill), demonstrating that the cgroup limit is
   actually enforced and not just a cosmetic Docker parameter.
4. Shows how to manually inspect, from the host, the real cgroup v2
   file that Docker created for a live container (`memory.max`,
   `memory.current`), the exact equivalent of `memory.limit_in_bytes`
   mentioned in the post but with cgroups v2 syntax.
5. Lists the kernel namespaces (PID, network, mount, IPC, UTS, user, cgroup,
   time) as a reference for the same namespaces that isolate a
   container.

## Requirements

- Docker (tested with Docker 29.x). No root is needed on the host beyond
  the usual permissions to use `docker`.
- A kernel with **cgroup v2** enabled (default on Ubuntu 22.04+,
  Debian 12+, recent Fedora, etc). You can verify it with:
  ```bash
  stat -fc %T /sys/fs/cgroup/
  # should print: cgroup2fs
  ```

## How to run it

```bash
cd administracion-avanzada-de-sistemas-linux--domina-linux-avanzado
./demo-cgroups-namespaces.sh
```

The script:
- Builds the `linux-avanzado-cgroups-demo` image from the `Dockerfile`.
- Runs the test container (takes ~20 seconds) and shows the log
  live.
- Counts how many times the kernel killed the process due to OOM.
- Lists the namespaces of the current host process, as a reference.
- Prints instructions to manually inspect the real cgroup of a
  live container.

For step 4 (manual inspection of a live cgroup), you can try it
yourself in parallel:

```bash
CID=$(docker run -d --memory=100m alpine sleep 60)
cat /sys/fs/cgroup/system.slice/docker-${CID}.scope/memory.max
cat /sys/fs/cgroup/system.slice/docker-${CID}.scope/memory.current
docker stop ${CID}
```

## Expected output

In the container section you will see lines like these repeated several
times (the exact number varies by machine):

```
stress-ng: debug: [7] vm: assuming killed by OOM killer, restarting again (instance 0)
stress-ng: debug: [7] vm: child died: signal 9 'SIGKILL' (instance 0)
```

And at the end:

```
El kernel mató el proceso 302 vez/veces por exceder el límite
de memoria del cgroup (100M), aunque pedía 150M. stress-ng reintenta
el stressor tras cada muerte, por eso el contenedor sigue corriendo
hasta el timeout en vez de terminar con código 137 de una sola vez.
Esto confirma que el límite del cgroup es real y lo aplica el kernel.
```

For the manual example `docker run -d --memory=100m alpine sleep 60`, the
output of `memory.max` and `memory.current` are values in bytes, for example:

```
104857600
892928
```

(104857600 bytes = 100 MB, the configured limit; the second value is the
memory actually in use by the container at that moment).

## Notes

- Does not require accounts or credentials from any cloud provider.
- Everything runs locally with Docker, no paid dependencies.
- The exact cgroup path (`/sys/fs/cgroup/system.slice/docker-<id>.scope/`)
  may vary slightly depending on the distro/Docker version if it uses a
  cgroup driver other than `systemd` (e.g. `cgroupfs`); in that case
  look for the container ID under `/sys/fs/cgroup/docker/<id>/`.

---

## 🇪🇸 Versión en español

# Cgroups y namespaces en la práctica

Ejemplo ejecutable para el post [Administración Avanzada de Sistemas Linux: Domina Linux Avanzado](https://www.devopsfreelance.pro/blog/posts/administracion-avanzada-de-sistemas-linux--domina-linux-avanzado/).

## Qué demuestra

El post explica cgroups y namespaces creando cgroups a mano con `mkdir` en
`/sys/fs/cgroup/`. Este ejemplo muestra que Docker no es más que una capa de
automatización sobre esos mismos mecanismos del kernel, y lo prueba en la
práctica:

1. Construye una imagen con `stress-ng` que intenta reservar 150 MB de RAM.
2. La corre en un contenedor con un límite de memoria de 100 MB
   (`--memory=100m`), es decir, un cgroup real creado por Docker.
3. Confirma en el log que el kernel mata el proceso repetidas veces por
   exceder el límite (OOM-kill), demostrando que el límite del cgroup se
   aplica de verdad y no es solo un parámetro cosmético de Docker.
4. Muestra cómo inspeccionar a mano, desde el host, el archivo de cgroup v2
   real que Docker creó para un contenedor vivo (`memory.max`,
   `memory.current`), el equivalente exacto a `memory.limit_in_bytes` que
   menciona el post pero con la sintaxis de cgroups v2.
5. Lista los namespaces del kernel (PID, red, mount, IPC, UTS, user, cgroup,
   time) como referencia de los mismos namespaces que aíslan a un
   contenedor.

## Requisitos

- Docker (probado con Docker 29.x). No hace falta ser root en el host más
  allá de los permisos habituales para usar `docker`.
- Un kernel con **cgroup v2** habilitado (por defecto en Ubuntu 22.04+,
  Debian 12+, Fedora reciente, etc). Se puede verificar con:
  ```bash
  stat -fc %T /sys/fs/cgroup/
  # debe imprimir: cgroup2fs
  ```

## Cómo correrlo

```bash
cd administracion-avanzada-de-sistemas-linux--domina-linux-avanzado
./demo-cgroups-namespaces.sh
```

El script:
- Construye la imagen `linux-avanzado-cgroups-demo` a partir del `Dockerfile`.
- Corre el contenedor de prueba (tarda ~20 segundos) y muestra el log en
  vivo.
- Cuenta cuántas veces el kernel mató el proceso por OOM.
- Lista los namespaces del proceso actual del host, a modo de referencia.
- Imprime instrucciones para inspeccionar a mano el cgroup real de un
  contenedor vivo.

Para el paso 4 (inspección manual de un cgroup vivo), podés probarlo vos
mismo en paralelo:

```bash
CID=$(docker run -d --memory=100m alpine sleep 60)
cat /sys/fs/cgroup/system.slice/docker-${CID}.scope/memory.max
cat /sys/fs/cgroup/system.slice/docker-${CID}.scope/memory.current
docker stop ${CID}
```

## Salida esperada

En la sección del contenedor vas a ver líneas como estas repetidas varias
veces (el número exacto varía según la máquina):

```
stress-ng: debug: [7] vm: assuming killed by OOM killer, restarting again (instance 0)
stress-ng: debug: [7] vm: child died: signal 9 'SIGKILL' (instance 0)
```

Y al final:

```
El kernel mató el proceso 302 vez/veces por exceder el límite
de memoria del cgroup (100M), aunque pedía 150M. stress-ng reintenta
el stressor tras cada muerte, por eso el contenedor sigue corriendo
hasta el timeout en vez de terminar con código 137 de una sola vez.
Esto confirma que el límite del cgroup es real y lo aplica el kernel.
```

Para el ejemplo manual de `docker run -d --memory=100m alpine sleep 60`, la
salida de `memory.max` y `memory.current` son valores en bytes, por ejemplo:

```
104857600
892928
```

(104857600 bytes = 100 MB, el límite configurado; el segundo valor es la
memoria realmente en uso por el contenedor en ese momento).

## Notas

- No requiere cuentas ni credenciales de ningún proveedor cloud.
- Todo corre localmente con Docker, sin dependencias pagas.
- El path exacto del cgroup (`/sys/fs/cgroup/system.slice/docker-<id>.scope/`)
  puede variar levemente según la distro/versión de Docker si usa un
  cgroup driver distinto a `systemd` (por ejemplo `cgroupfs`); en ese caso
  buscá el ID del contenedor bajo `/sys/fs/cgroup/docker/<id>/`.
