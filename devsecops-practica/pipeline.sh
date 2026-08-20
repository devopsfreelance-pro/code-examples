#!/usr/bin/env bash
#
# Mini pipeline DevSecOps: reproduce localmente las etapas descriptas en el
# post (Commit -> SAST, Build -> escaneo de dependencias, Deploy -> escaneo
# de contenedores) usando solo Docker, sin instalar nada en el host.
#
# Uso: ./pipeline.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${SCRIPT_DIR}/app"
IMAGE_NAME="devsecops-practica-app:latest"

fail=0

echo "=================================================================="
echo "1) SAST - Análisis estático de código con Bandit (etapa: Commit)"
echo "=================================================================="
if ! docker run --rm -v "${APP_DIR}:/src:ro" python:3.11-slim \
  bash -c "pip install --quiet bandit && bandit -r /src -f txt"; then
  echo ">> Bandit encontró hallazgos (esperado: eval(), shell=True)."
  fail=1
fi

echo
echo "=================================================================="
echo "2) Escaneo de secretos con Gitleaks (etapa: Commit)"
echo "=================================================================="
if ! docker run --rm -v "${SCRIPT_DIR}:/repo:ro" zricethezav/gitleaks:latest \
  detect --source /repo --no-git -v; then
  echo ">> Gitleaks encontró secretos (esperado: AWS key de ejemplo en app.py)."
  fail=1
fi

echo
echo "=================================================================="
echo "3) Escaneo de dependencias con Trivy (etapa: Build)"
echo "=================================================================="
if ! docker run --rm -v "${APP_DIR}:/src:ro" aquasec/trivy:latest \
  fs --severity HIGH,CRITICAL /src; then
  echo ">> Trivy encontró CVEs en las dependencias (esperado: Flask/requests viejos)."
  fail=1
fi

echo
echo "=================================================================="
echo "4) Build de la imagen (etapa: Build)"
echo "=================================================================="
docker build -t "${IMAGE_NAME}" "${APP_DIR}"

echo
echo "=================================================================="
echo "5) Escaneo de la imagen con Trivy (etapa: Deploy)"
echo "=================================================================="
if ! docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest \
  image --severity HIGH,CRITICAL "${IMAGE_NAME}"; then
  echo ">> Trivy encontró CVEs en la imagen construida."
  fail=1
fi

echo
echo "=================================================================="
if [ "${fail}" -ne 0 ]; then
  echo "Pipeline DevSecOps: se detectaron hallazgos de seguridad (comportamiento"
  echo "esperado en este demo). En un pipeline real, estos hallazgos bloquearían"
  echo "el merge/deploy (shift left)."
else
  echo "Pipeline DevSecOps: sin hallazgos."
fi
echo "=================================================================="
