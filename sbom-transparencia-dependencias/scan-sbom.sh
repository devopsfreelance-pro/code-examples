#!/usr/bin/env bash
# Escanea el SBOM generado por generate-sbom.sh contra la base de datos de
# vulnerabilidades de Grype (Anchore), sin instalar el binario localmente.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SBOM_FILE="${SCRIPT_DIR}/sbom.cyclonedx.json"

if [[ ! -f "${SBOM_FILE}" ]]; then
  echo "ERROR: no se encontró ${SBOM_FILE}. Corré primero ./generate-sbom.sh" >&2
  exit 1
fi

echo "==> Escaneando ${SBOM_FILE} con Grype (Anchore)"

docker run --rm \
  -v "${SCRIPT_DIR}:/analisis:ro" \
  anchore/grype:latest \
  sbom:/analisis/sbom.cyclonedx.json -o table
