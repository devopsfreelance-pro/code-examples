# Linux resource management with cgroups: runnable demo

Post: [Linux Resource Management with cgroups and systemd](https://www.devopsfreelance.pro/blog/en/posts/linux-resource-management-cgroups-systemd/)

## What this example demonstrates

The post explains that **cgroups** is the kernel mechanism that limits CPU and
memory per process group, and that **systemd** (with `CPUQuota=`,
`MemoryMax=`) and **Docker** (with `--cpus`, `--memory`) are two different
ways of configuring that same mechanism.

This example spins up two containers with `stress-ng` that try to consume
more CPU and more memory than they're allowed, and shows live how cgroups
enforces the limit:

- **`cpu-limitado`**: requests 2 cores at 100% but the cgroup only grants it
  0.5 CPU (`cpus: "0.5"` in Compose, equivalent to `CPUQuota=50%` in a
  systemd unit).
- **`mem-limitado`**: tries to reserve 300MB but the cgroup only allows it
  100MB (`mem_limit: 100m` in Compose, equivalent to `MemoryMax=100M`). The
  kernel kills the process via OOM inside the cgroup before it can affect the
  rest of the system.

It also includes `systemd-run-demo.sh`, an optional script to see the same
limit applied directly with `systemd-run` on a Linux machine with systemd
(without going through Docker), which is exactly the production use case the
post describes.

## Requirements

- Docker with Docker Compose v2 (`docker compose version`)
- Native Linux (on macOS/Windows with Docker Desktop, `mem-limitado` may not
  kill the process because the internal VM manages memory differently)
- Optional, for `systemd-run-demo.sh`: Linux with systemd as PID 1 and
  `stress-ng` installed (`sudo apt install stress-ng` or
  `sudo dnf install stress-ng`)

## How to run it

```bash
cd gestion-recursos-sistemas-linux
chmod +x run-demo.sh
./run-demo.sh
```

The script does, in order:

1. Builds the image (`alpine` + `stress-ng`).
2. Runs `cpu-limitado`: requests 2 cores, the cgroup gives it 0.5.
3. Runs `mem-limitado`: requests 300MB, the cgroup gives it 100MB and kills it.
4. Cleans up the containers.

You can also run each service separately:

```bash
docker compose build
docker compose run --rm cpu-limitado
docker compose run --rm mem-limitado
```

And, if you're on Linux with systemd and want to see the same limit without
Docker:

```bash
chmod +x systemd-run-demo.sh
./systemd-run-demo.sh
```

## Expected output

In `cpu-limitado`, `stress-ng --metrics-brief` reports the actual time used
by the workers. With the 0.5 CPU limit, the "bogo ops/s" and the real CPU
usage stay capped at ~50% of one core, even though 2 cores at 100% were
requested:

```
demo-cpu-limitado  |  stress-ng: info:  [1] setting to a 20 second run per stressor
demo-cpu-limitado  |  stress-ng: info:  [1] dispatching hogs: 2 cpu
demo-cpu-limitado  |  stress-ng: info:  [1] cpu:            ... (bogo ops/s bajo por el throttling)
demo-cpu-limitado  |  stress-ng: info:  [1] successful run completed in 20.00s
```

In `mem-limitado`, the container exits with a nonzero exit code (`Killed`,
exit code 137) because the kernel triggered the cgroup's OOM killer once it
exceeded the 100MB limit:

```
demo-mem-limitado  |  stress-ng: info:  [1] dispatching hogs: 1 vm
demo-mem-limitado  |  stress-ng: info:  [1] vm: stress-ng-vm: got SIGKILL...
   -> El proceso murio (exit code 137), como se espera:
      cgroups impidio que superara los 100MB asignados.
```

You can confirm the exact reason for the kill with:

```bash
docker inspect demo-mem-limitado --format '{{.State.OOMKilled}}'
```

## Relation to the post

This reproduces in miniature what the post describes with:

```ini
[Service]
CPUQuota=50%
MemoryLimit=1G
```

Docker Compose (`cpus:`, `mem_limit:`) and systemd (`CPUQuota=`,
`MemoryMax=`) configure the same underlying cgroups controller; the only
difference is the declarative layer you use to write the limit.

---

## 🇪🇸 Versión en español

# Gestión de recursos en Linux con cgroups: demo ejecutable

Post: [Gestión de Recursos en Linux: CPU, Memoria y Disco con cgroups y systemd](https://www.devopsfreelance.pro/blog/posts/gestion-recursos-sistemas-linux/)

## Qué demuestra este ejemplo

El post explica que **cgroups** es el mecanismo del kernel que limita CPU y
memoria por grupo de procesos, y que **systemd** (con `CPUQuota=`,
`MemoryMax=`) y **Docker** (con `--cpus`, `--memory`) son dos formas
distintas de configurar ese mismo mecanismo.

Este ejemplo levanta dos contenedores con `stress-ng` que intentan consumir
más CPU y más memoria de la que tienen permitida, y muestra en vivo cómo
cgroups aplica el límite:

- **`cpu-limitado`**: pide 2 cores al 100% pero el cgroup solo le concede
  0.5 CPU (`cpus: "0.5"` en Compose, equivalente a `CPUQuota=50%` en una
  unit de systemd).
- **`mem-limitado`**: intenta reservar 300MB pero el cgroup solo le permite
  100MB (`mem_limit: 100m` en Compose, equivalente a `MemoryMax=100M`). El
  kernel mata el proceso por OOM dentro del cgroup antes de que afecte al
  resto del sistema.

Incluye además `systemd-run-demo.sh`, un script opcional para ver el mismo
límite aplicado directamente con `systemd-run` en una máquina Linux con
systemd (sin pasar por Docker), que es justo el caso de uso que describe el
post para servicios en producción.

## Requisitos

- Docker con Docker Compose v2 (`docker compose version`)
- Linux nativo (en macOS/Windows con Docker Desktop, `mem-limitado` puede no
  matar el proceso porque la VM interna gestiona la memoria distinto)
- Opcional, para `systemd-run-demo.sh`: Linux con systemd como PID 1 y
  `stress-ng` instalado (`sudo apt install stress-ng` o
  `sudo dnf install stress-ng`)

## Cómo correrlo

```bash
cd gestion-recursos-sistemas-linux
chmod +x run-demo.sh
./run-demo.sh
```

El script hace, en orden:

1. Build de la imagen (`alpine` + `stress-ng`).
2. Corre `cpu-limitado`: pide 2 cores, el cgroup le da 0.5.
3. Corre `mem-limitado`: pide 300MB, el cgroup le da 100MB y lo mata.
4. Limpieza de contenedores.

También podés correr cada servicio por separado:

```bash
docker compose build
docker compose run --rm cpu-limitado
docker compose run --rm mem-limitado
```

Y, si estás en Linux con systemd y querés ver el mismo límite sin Docker:

```bash
chmod +x systemd-run-demo.sh
./systemd-run-demo.sh
```

## Salida esperada

En `cpu-limitado`, `stress-ng --metrics-brief` reporta el tiempo real usado
por los workers. Con el límite de 0.5 CPU, el "bogo ops/s" y el uso de CPU
real quedan acotados a ~50% de un core, aunque se pidieron 2 cores al 100%:

```
demo-cpu-limitado  |  stress-ng: info:  [1] setting to a 20 second run per stressor
demo-cpu-limitado  |  stress-ng: info:  [1] dispatching hogs: 2 cpu
demo-cpu-limitado  |  stress-ng: info:  [1] cpu:            ... (bogo ops/s bajo por el throttling)
demo-cpu-limitado  |  stress-ng: info:  [1] successful run completed in 20.00s
```

En `mem-limitado`, el contenedor termina con código de salida distinto de
cero (`Killed`, exit code 137) porque el kernel disparó el OOM killer del
cgroup al superar los 100MB:

```
demo-mem-limitado  |  stress-ng: info:  [1] dispatching hogs: 1 vm
demo-mem-limitado  |  stress-ng: info:  [1] vm: stress-ng-vm: got SIGKILL...
   -> El proceso murio (exit code 137), como se espera:
      cgroups impidio que superara los 100MB asignados.
```

Podés confirmar el motivo exacto del kill con:

```bash
docker inspect demo-mem-limitado --format '{{.State.OOMKilled}}'
```

## Relación con el post

Esto reproduce en miniatura lo que el post describe con:

```ini
[Service]
CPUQuota=50%
MemoryLimit=1G
```

Docker Compose (`cpus:`, `mem_limit:`) y systemd (`CPUQuota=`,
`MemoryMax=`) configuran el mismo controlador de cgroups por debajo; la
diferencia es solo la capa declarativa que usás para escribir el límite.
