#!/bin/bash
# Orquestacion de security testing automatizado sobre la mini app de ejemplo.
#
# Ejecuta dos de las capas descriptas en el post usando SOLO Docker
# (sin instalar nada localmente ni usar servicios pagos):
#   1. SAST con Semgrep sobre app/app.py
#   2. Escaneo de imagen de contenedor con Trivy
#
# Uso: ./security-scan.sh

set -e

IMAGE_NAME="vulnerable-app:test"
REPORT_DIR="security-reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$REPORT_DIR"

echo "=== Iniciando Security Testing Pipeline (demo local) ==="

echo ""
echo "--- 1/2: Analisis SAST con Semgrep ---"
docker run --rm \
    -v "$(pwd)/app:/src" \
    returntocorp/semgrep:latest \
    semgrep --config=p/security-audit --config=p/owasp-top-ten \
    --error \
    --json --output=/src/../"$REPORT_DIR"/semgrep-"$TIMESTAMP".json \
    /src \
    || SEMGREP_EXIT=$?

SEMGREP_EXIT=${SEMGREP_EXIT:-0}
if [ "$SEMGREP_EXIT" -ne 0 ]; then
    echo "Semgrep encontro hallazgos (ver $REPORT_DIR/semgrep-$TIMESTAMP.json)"
else
    echo "Semgrep no encontro hallazgos bloqueantes"
fi

echo ""
echo "--- 2/2: Build + escaneo de contenedor con Trivy ---"
docker build -t "$IMAGE_NAME" .

docker run --rm \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$(pwd)/$REPORT_DIR":/reports \
    aquasec/trivy:latest image \
    --severity HIGH,CRITICAL \
    --format json \
    --output /reports/trivy-"$TIMESTAMP".json \
    "$IMAGE_NAME"

CRITICAL_COUNT=$(grep -o '"Severity":"CRITICAL"' "$REPORT_DIR"/trivy-"$TIMESTAMP".json | wc -l)
HIGH_COUNT=$(grep -o '"Severity":"HIGH"' "$REPORT_DIR"/trivy-"$TIMESTAMP".json | wc -l)

echo ""
echo "=== Resumen ==="
echo "Reportes generados en: $REPORT_DIR/"
echo "Semgrep: hallazgos SAST en app/app.py (inyeccion SQL + secreto hardcodeado esperados)"
echo "Trivy: $CRITICAL_COUNT vulnerabilidades CRITICAL, $HIGH_COUNT HIGH en la imagen base"

if [ "$SEMGREP_EXIT" -ne 0 ] || [ "$CRITICAL_COUNT" -gt 0 ]; then
    echo ""
    echo "FALLO: se encontraron vulnerabilidades. Revisa $REPORT_DIR/"
    exit 1
fi

echo ""
echo "EXITO: no se encontraron vulnerabilidades criticas"
exit 0
