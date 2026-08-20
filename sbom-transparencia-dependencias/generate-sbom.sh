#!/usr/bin/env bash
# Genera un SBOM (formato CycloneDX JSON) del directorio sample-app usando Syft
# vía Docker, sin necesidad de instalar el binario localmente.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${SCRIPT_DIR}/sample-app"
OUTPUT_FILE="${SCRIPT_DIR}/sbom.cyclonedx.json"

echo "==> Generando SBOM de ${APP_DIR} con Syft (Anchore)"

docker run --rm \
  -v "${APP_DIR}:/proyecto:ro" \
  anchore/syft:latest \
  packages dir:/proyecto -o cyclonedx-json > "${OUTPUT_FILE}"

echo "==> SBOM generado en: ${OUTPUT_FILE}"
echo "==> Componentes detectados:"
grep -o '"name": *"[^"]*"' "${OUTPUT_FILE}" | sort -u || true
