#!/usr/bin/env bash
# Demo opcional (solo Linux con systemd, sin Docker): aplica los mismos
# limites de CPU/memoria directamente con systemd-run, que crea una unit
# transient respaldada por un cgroup.
#
# Requiere: systemd, stress-ng instalado (apt install stress-ng /
# dnf install stress-ng), y systemd corriendo como PID 1 (no funciona
# dentro de contenedores ni en WSL sin systemd habilitado).
set -euo pipefail

if ! command -v stress-ng >/dev/null 2>&1; then
  echo "stress-ng no esta instalado. Instalalo con:"
  echo "  sudo apt install stress-ng   # Debian/Ubuntu"
  echo "  sudo dnf install stress-ng   # Fedora/RHEL"
  exit 1
fi

if ! pidof systemd >/dev/null 2>&1; then
  echo "Este script requiere systemd como PID 1 (no funciona en contenedores)."
  exit 1
fi

echo "== Proceso limitado a 0.5 CPU via systemd-run (CPUQuota=50%) =="
sudo systemd-run --scope -p CPUQuota=50% \
  stress-ng --cpu 2 --cpu-load 100 --timeout 15s --metrics-brief

echo
echo "== Proceso limitado a 100MB via systemd-run (MemoryMax=100M) =="
echo "   Debe ser matado por OOM del cgroup al pasar los 100MB."
set +e
sudo systemd-run --scope -p MemoryMax=100M -p MemorySwapMax=0 \
  stress-ng --vm 1 --vm-bytes 300M --vm-keep --timeout 15s --metrics-brief
exit_code=$?
set -e

echo
if [ "$exit_code" -ne 0 ]; then
  echo "-> Exit code $exit_code: el cgroup del scope mato al proceso, como se espera."
else
  echo "-> El proceso no fue matado. Revisa si cgroups v2 esta activo:"
  echo "   cat /sys/fs/cgroup/cgroup.controllers"
fi
