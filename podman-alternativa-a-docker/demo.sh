#!/usr/bin/env bash
# Demo del post "Podman: Alternativa Segura y Moderna a Docker".
#
# Ilustra el concepto central del post:
#   1. Construir y correr un contenedor ROOTLESS con Podman (sin dockerd,
#      sin root).
#   2. Verificar que, aunque el proceso ve UID 0 adentro del contenedor,
#      en el HOST corre con un UID normal sin privilegios (subordinate
#      UIDs / user namespaces).
#   3. Generar un manifiesto de Kubernetes directamente desde el
#      contenedor en ejecucion (`podman generate kube`), la capacidad
#      que el post menciona como ventaja frente a Docker para pasar de
#      local a Kubernetes.
#
# Requiere: podman instalado (ver README para instalacion).
set -euo pipefail

IMAGE_NAME="podman-demo:latest"
CONTAINER_NAME="podman-demo"
PORT="8080"

echo "==> 1) Construyendo la imagen con Podman (equivalente a docker build)"
podman build -f Containerfile -t "${IMAGE_NAME}" .

echo
echo "==> 2) Corriendo el contenedor en modo rootless"
podman run -d --name "${CONTAINER_NAME}" -p "${PORT}:8080" "${IMAGE_NAME}"

echo
echo "==> 3) UID del proceso visto desde el HOST (fuera del contenedor)"
echo "    Deberia ser un UID sin privilegios (no 0), aunque adentro el proceso se vea como root/UID configurado."
podman top "${CONTAINER_NAME}" huser pid comm

echo
echo "==> 4) Probando el servicio"
sleep 1
curl -s "http://localhost:${PORT}/" || echo "(si curl falla, probar manualmente: curl http://localhost:${PORT}/)"

echo
echo "==> 5) Generando manifiesto de Kubernetes desde el contenedor en ejecucion"
podman generate kube "${CONTAINER_NAME}" > podman-kube.yaml
echo "    Manifiesto guardado en podman-kube.yaml"

echo
echo "==> 6) Limpieza"
podman stop "${CONTAINER_NAME}" >/dev/null
podman rm "${CONTAINER_NAME}" >/dev/null
echo "    Contenedor detenido y eliminado. La imagen '${IMAGE_NAME}' y el archivo podman-kube.yaml quedan disponibles."
