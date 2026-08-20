# Linux Kernel Tuning with sysctl - Runnable Example

Post: [Linux Kernel Tuning: Optimize Performance with sysctl](https://www.devopsfreelance.pro/blog/en/posts/linux-kernel-tuning/)

## What this demonstrates

The post covers dozens of `sysctl` parameters (network, memory, filesystem, etc.)
but applying them to a real kernel requires `sudo` and modifies an entire
machine, which is not something that can be requested safely in a blog example.

This example uses a safe, 100% reproducible alternative: the `net.*`
parameters that are "namespaced" (one per Linux network namespace) can be
applied per-container with Docker, without `--privileged` and without
touching the host kernel. It spins up two identical nginx containers, one
without tuning and one with a real subset of the parameters from the post
(`net.core.somaxconn`, `net.ipv4.tcp_fin_timeout`, `net.ipv4.tcp_syncookies`,
`net.ipv4.ip_local_port_range`), plus a script that reads the effective
values of each one with `sysctl -n` inside each container to compare
"before" and "after" in practice.

## Requirements

- Docker with Compose v2 support (`docker compose version`)
- No `sudo` required on the host, no privileged permissions

## Files

- `docker-compose.yml` - two nginx services: `nginx-default` (no tuning) and
  `nginx-tuned` (with the `sysctls:` key applying the parameters from the post)
- `sysctl.d/99-tuning-demo.conf` - the same parameters in the real
  configuration file format used by `/etc/sysctl.d/`, as a reference for how
  they'd be applied on a real server (`sudo sysctl --system`)
- `compare-sysctl.sh` - compares the effective sysctl values between both
  containers

## Steps to run it

```bash
# 1. Levantar los dos contenedores
docker compose up -d

# 2. Comparar los parametros de sysctl entre el contenedor sin tuning
#    y el contenedor tuneado
./compare-sysctl.sh

# 3. Limpiar
docker compose down
```

## Expected output

```
Parametro                        | nginx-default        | nginx-tuned
-------------------------------------------------------------------
net.core.somaxconn               | 4096                 | 65535
net.ipv4.tcp_fin_timeout         | 60                   | 15
net.ipv4.tcp_syncookies          | 1                    | 1
net.ipv4.ip_local_port_range     | 32768	60999          | 1024	65535
```

The exact values in the `nginx-default` column may vary depending on the
host's distribution and Docker/kernel version (for example, `somaxconn`
may come in as 128 or 4096), but the `nginx-tuned` column will always
reflect exactly the values defined in `docker-compose.yml`.

## Taking it to a real server

On a server (not a container), the same parameters are applied by copying
`sysctl.d/99-tuning-demo.conf` to `/etc/sysctl.d/` and running:

```bash
sudo cp sysctl.d/99-tuning-demo.conf /etc/sysctl.d/
sudo sysctl --system
```

See the full post for the rest of the parameters (memory, filesystem,
Kubernetes) and the recommended methodology for applying them in production.

---

## 🇪🇸 Versión en español

# Tuning del Kernel Linux con sysctl - Ejemplo ejecutable

Post: [Tuning del Kernel Linux: Optimiza Rendimiento con sysctl y Parámetros Clave](https://www.devopsfreelance.pro/blog/posts/tunning-kernel-linux/)

## Qué demuestra

El post explica decenas de parametros de `sysctl` (red, memoria, filesystem, etc.)
pero aplicarlos sobre un kernel real requiere `sudo` y modifica una maquina
completa, algo que no se puede pedir de forma segura en un ejemplo de blog.

Este ejemplo usa una alternativa segura y 100% reproducible: los parametros
`net.*` que son "namespaced" (uno por cada namespace de red de Linux) se
pueden aplicar por-contenedor con Docker, sin `--privileged` y sin tocar el
kernel del host. Levanta dos contenedores nginx identicos, uno sin tuning y
otro con un subconjunto real de los parametros del post
(`net.core.somaxconn`, `net.ipv4.tcp_fin_timeout`, `net.ipv4.tcp_syncookies`,
`net.ipv4.ip_local_port_range`), y un script que lee los valores efectivos de
cada uno con `sysctl -n` dentro de cada contenedor para comparar el "antes" y
el "despues" en la practica.

## Requisitos

- Docker con soporte de Compose v2 (`docker compose version`)
- No requiere `sudo` en el host ni permisos privilegiados

## Archivos

- `docker-compose.yml` - dos servicios nginx: `nginx-default` (sin tuning) y
  `nginx-tuned` (con la clave `sysctls:` aplicando los parametros del post)
- `sysctl.d/99-tuning-demo.conf` - los mismos parametros en formato de archivo
  de configuracion real de `/etc/sysctl.d/`, como referencia de como se
  aplicarian en un servidor de verdad (`sudo sysctl --system`)
- `compare-sysctl.sh` - compara los valores efectivos de sysctl entre ambos
  contenedores

## Pasos para correrlo

```bash
# 1. Levantar los dos contenedores
docker compose up -d

# 2. Comparar los parametros de sysctl entre el contenedor sin tuning
#    y el contenedor tuneado
./compare-sysctl.sh

# 3. Limpiar
docker compose down
```

## Salida esperada

```
Parametro                        | nginx-default        | nginx-tuned
-------------------------------------------------------------------
net.core.somaxconn               | 4096                 | 65535
net.ipv4.tcp_fin_timeout         | 60                   | 15
net.ipv4.tcp_syncookies          | 1                    | 1
net.ipv4.ip_local_port_range     | 32768	60999          | 1024	65535
```

Los valores exactos de la columna `nginx-default` pueden variar segun la
distribucion y version de Docker/kernel del host (por ejemplo `somaxconn`
puede venir en 128 o 4096), pero la columna `nginx-tuned` siempre va a
reflejar exactamente los valores definidos en `docker-compose.yml`.

## Llevarlo a un servidor real

En un servidor (no en un contenedor), los mismos parametros se aplican
copiando `sysctl.d/99-tuning-demo.conf` a `/etc/sysctl.d/` y ejecutando:

```bash
sudo cp sysctl.d/99-tuning-demo.conf /etc/sysctl.d/
sudo sysctl --system
```

Ver el post completo para el resto de los parametros (memoria, filesystem,
Kubernetes) y la metodologia recomendada para aplicarlos en produccion.
