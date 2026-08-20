#!/usr/bin/env bash
# Simula 3 ciclos kaizen consecutivos sobre el mismo modulo: en cada
# ciclo se reemplaza sample_app/calculator.py por la version de la
# siguiente iteracion (sample_app/iterations/vN_calculator.py) y se
# corre el mismo pipeline de metricas que describe el post
# (pylint + radon + pytest --cov), igual que en el bloque YAML de la
# seccion "Implementacion de pipelines de mejora continua".
set -euo pipefail

cd "$(dirname "$0")"

rm -f metrics_history.json coverage.json

for v in v1 v2 v3; do
    cp "sample_app/iterations/${v}_calculator.py" "sample_app/calculator.py"
    python3 scripts/collect_metrics.py "$v"
done

echo
python3 scripts/show_trend.py
