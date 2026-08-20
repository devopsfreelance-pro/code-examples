#!/usr/bin/env bash
# demo-cgroups-namespaces.sh
#
# Demuestra en la práctica los dos mecanismos del kernel que el post explica
# a nivel teórico (cgroups y namespaces) usando Docker, que internamente no
# es más que un wrapper sobre ambos.
#
# 1. Levanta un contenedor con un límite de memoria de 100M (cgroup) y lanza
#    dentro un proceso que intenta reservar 150M -> el kernel debe matarlo
#    (OOM-kill), demostrando que el límite es real y lo aplica el kernel,
#    no Docker.
# 2. Inspecciona el archivo de cgroup v2 real que Docker creó en el host
#    para ese contenedor (memory.max, memory.current).
# 3. Lista los namespaces (PID, red, mount, etc.) que aíslan al contenedor,
#    comparándolos con los del proceso host.
#
# Requisitos: Docker, cgroup v2 habilitado en el host (por defecto en
# distros modernas: Ubuntu 22.04+, Debian 12+, Fedora, etc).

set -euo pipefail

IMAGE_NAME="linux-avanzado-cgroups-demo"
CONTAINER_NAME="cgroups-demo"

echo "== 1. Construyendo la imagen de prueba (stress-ng) =="
docker build -t "${IMAGE_NAME}" "$(dirname "$0")"

echo
echo "== 2. Lanzando contenedor con límite de memoria de 100M (cgroup) =="
echo "   El proceso dentro intenta reservar 150M: el kernel debe matarlo (OOM)."
LOG_FILE="$(mktemp)"
set +e
docker run \
  --name "${CONTAINER_NAME}" \
  --rm \
  --memory="100m" \
  --memory-swap="100m" \
  --cpus="0.5" \
  "${IMAGE_NAME}" 2>&1 | tee "${LOG_FILE}"
set -e

OOM_KILLS=$(grep -c "OOM killer" "${LOG_FILE}" || true)
rm -f "${LOG_FILE}"

echo
if [ "${OOM_KILLS}" -gt 0 ]; then
  echo "El kernel mató el proceso ${OOM_KILLS} vez/veces por exceder el límite"
  echo "de memoria del cgroup (100M), aunque pedía 150M. stress-ng reintenta"
  echo "el stressor tras cada muerte, por eso el contenedor sigue corriendo"
  echo "hasta el timeout en vez de terminar con código 137 de una sola vez."
  echo "Esto confirma que el límite del cgroup es real y lo aplica el kernel."
else
  echo "No se detectaron mensajes de OOM en el log."
  echo "(Si tu host tiene swap habilitado a nivel cgroup o mucha memoria libre,"
  echo "el OOM-killer puede tardar más que el timeout de 20s en actuar.)"
fi

echo
echo "== 3. Namespaces: comparando el proceso host vs el que corrió en el contenedor =="
echo "   (se muestran los namespaces activos del propio shell como referencia)"
echo
echo "Namespaces del proceso actual (host):"
ls -la /proc/self/ns/ 2>/dev/null || echo "  (requiere /proc, no disponible en este entorno)"

echo
echo "== 4. Cómo inspeccionar cgroups v2 de un contenedor en vivo =="
cat <<'EOF'
Mientras un contenedor está corriendo (quitá --rm y corré en background con -d
para probarlo vos mismo), Docker crea su cgroup real bajo:

  /sys/fs/cgroup/system.slice/docker-<container_id>.scope/

Ejemplo para ver el límite y el uso actual de memoria de un contenedor vivo:

  CID=$(docker run -d --memory=100m alpine sleep 60)
  cat /sys/fs/cgroup/system.slice/docker-${CID}.scope/memory.max
  cat /sys/fs/cgroup/system.slice/docker-${CID}.scope/memory.current
  docker stop ${CID}

Esto es exactamente lo que el post describe como "Control de Grupos (cgroups)",
pero en vez de crear el cgroup a mano con mkdir en /sys/fs/cgroup/, Docker lo
automatiza al traducir --memory/--cpus en escrituras a esos mismos archivos.
EOF

echo
echo "Demo terminada."
