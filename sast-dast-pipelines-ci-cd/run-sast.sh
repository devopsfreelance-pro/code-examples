#!/usr/bin/env bash
# SAST: analiza app.py con Semgrep (regla de seguridad p/security-audit)
# SIN ejecutar la aplicacion, tal como describe el post.
set -euo pipefail

cd "$(dirname "$0")"

echo "== SAST: Semgrep contra app.py (codigo estatico, app NO se ejecuta) =="

docker run --rm \
  -v "$(pwd)":/src \
  returntocorp/semgrep:latest \
  semgrep scan --config p/security-audit --config p/secrets --config p/sql-injection /src/app.py \
  --error \
  --output /src/sast-report.txt \
  --text

echo
echo "Reporte guardado en sast-report.txt"
echo "Semgrep termina con exit code != 0 si encuentra hallazgos (--error),"
echo "igual que en un pipeline real donde esto rompe el build."
