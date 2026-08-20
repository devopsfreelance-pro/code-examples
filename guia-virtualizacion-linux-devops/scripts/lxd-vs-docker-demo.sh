#!/usr/bin/env bash
# lxd-vs-docker-demo.sh
# Demuestra la diferencia de aislamiento entre un contenedor de sistema (LXD)
# y un contenedor de aplicacion (Docker): en LXD ves un sistema completo con
# systemd e init propio; en Docker ves un unico proceso aislado.
#
# Requisitos: snap (LXD) y/o docker instalados. El script detecta que hay
# disponible y corre la demo correspondiente; si estan ambos, corre las dos.
#
# Uso:
#   ./lxd-vs-docker-demo.sh

set -euo pipefail

run_lxd_demo() {
  echo "== Demo LXD: contenedor de sistema =="
  if ! command -v lxc >/dev/null 2>&1; then
    echo "LXD no instalado. Instalar con: sudo snap install lxd && sudo lxd init --auto"
    return 1
  fi

  echo "-> Creando contenedor 'demo-lxd' basado en Ubuntu 22.04"
  lxc launch ubuntu:22.04 demo-lxd >/dev/null

  echo "-> Esperando red..."
  for _ in $(seq 1 15); do
    if lxc exec demo-lxd -- true >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done

  echo "-> Procesos dentro del contenedor (nota systemd como PID 1):"
  lxc exec demo-lxd -- ps -eo pid,comm | head -n 8

  echo "-> Limitando recursos: 1 vCPU, 512MB RAM"
  lxc config set demo-lxd limits.cpu 1
  lxc config set demo-lxd limits.memory 512MB

  echo "-> Limpiando"
  lxc delete demo-lxd --force
  echo
}

run_docker_demo() {
  echo "== Demo Docker: contenedor de aplicacion =="
  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker no instalado. Instalar con: curl -fsSL https://get.docker.com | sh"
    return 1
  fi

  echo "-> Corriendo un unico proceso aislado (nginx)"
  docker run -d --name demo-docker --rm nginx:alpine >/dev/null

  echo "-> Procesos dentro del contenedor (nota: un solo proceso, no systemd):"
  docker exec demo-docker ps -eo pid,comm

  echo "-> Limpiando"
  docker stop demo-docker >/dev/null

  echo
}

echo "Comparando aislamiento LXC/LXD (contenedor de sistema) vs Docker (contenedor de aplicacion)"
echo

lxd_ok=0
docker_ok=0
run_lxd_demo && lxd_ok=1 || true
run_docker_demo && docker_ok=1 || true

if [ "$lxd_ok" -eq 0 ] && [ "$docker_ok" -eq 0 ]; then
  echo "Ninguna herramienta disponible. Instala LXD y/o Docker para correr la demo."
  exit 1
fi

echo "Listo. LXD expone un sistema operativo completo (systemd, multiples procesos);"
echo "Docker expone un unico proceso de aplicacion. Esa es la diferencia de aislamiento."
