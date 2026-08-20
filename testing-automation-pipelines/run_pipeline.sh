#!/usr/bin/env bash
#
# Simula un testing pipeline respetando la pirámide de testing:
#   1. Análisis estático (rápido, sin ejecutar el código)
#   2. Pruebas unitarias (rápidas, sin dependencias externas)
#   3. Pruebas de integración (más lentas, requieren Redis real)
#
# Si una etapa falla, el pipeline se detiene inmediatamente sin desperdiciar
# tiempo en las etapas siguientes, tal como se describe en el post.
set -euo pipefail

step() {
  echo ""
  echo "=== $1 ==="
}

step "Etapa 1/3: análisis estático (pyflakes)"
python3 -m pyflakes app.py test_unit.py test_integration.py

step "Etapa 2/3: pruebas unitarias (rápidas, sin dependencias externas)"
python3 -m pytest test_unit.py -v

step "Etapa 3/3: pruebas de integración (requieren Redis)"
python3 -m pytest test_integration.py -v

echo ""
echo "Pipeline completo: todas las etapas pasaron."
