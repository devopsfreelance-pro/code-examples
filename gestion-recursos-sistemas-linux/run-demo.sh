#!/usr/bin/env bash
# Demo: cgroups aplicando limites de CPU y memoria a un proceso, tal como
# lo hace systemd (CPUQuota/MemoryMax) o cualquier motor de contenedores.
#
# Docker usa cgroups por debajo para todo --cpus / --memory, asi que este
# script es una forma reproducible de ver el mismo mecanismo que describe
# el post sin tener que tocar cgroups a mano en el host.
set -euo pipefail

cd "$(dirname "$0")"

echo "== 1) Build de la imagen con stress-ng =="
docker compose build

echo
echo "== 2) Proceso limitado a 0.5 CPU (equivalente a CPUQuota=50%) =="
echo "   Pide 2 cores al 100% mientras cgroups solo le concede medio core."
docker compose run --rm cpu-limitado
echo "   -> Revisa 'cpu used per instance' en la salida: debe rondar ~50%"
echo "      del tiempo real, no el 200% que pediria sin limite."

echo
echo "== 3) Proceso limitado a 100MB de memoria (equivalente a MemoryMax=100M) =="
echo "   Intenta reservar 300MB; el kernel debe matarlo por OOM dentro del cgroup."
set +e
docker compose run --rm mem-limitado
exit_code=$?
set -e

echo
if [ "$exit_code" -ne 0 ]; then
  echo "   -> El proceso murio (exit code $exit_code), como se espera:"
  echo "      cgroups impidio que superara los 100MB asignados."
else
  echo "   -> El proceso termino sin ser matado. Revisa los limites de tu Docker Desktop"
  echo "      (en Linux nativo con cgroups v2 deberia fallar)."
fi

echo
echo "== 4) Limpieza =="
docker compose down --remove-orphans 2>/dev/null || true
echo "Listo."
