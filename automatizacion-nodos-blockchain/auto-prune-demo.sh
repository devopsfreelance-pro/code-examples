#!/bin/bash
# auto-prune-demo.sh
# Version demostrable del auto-prune.sh del post: en vez de medir el % de
# disco real (que no podemos controlar en una laptop), mide el tamano de un
# directorio de datos simulado contra un limite en MB. La logica de decision
# (umbral -> detener servicio -> "prunear" -> reiniciar servicio) es la misma
# que usarias en produccion con `df` y `geth snapshot prune-state`.
#
# Uso: ./auto-prune-demo.sh <directorio-datos> <limite-mb> <umbral-pct>
# Ejemplo: ./auto-prune-demo.sh ./data 100 85

set -euo pipefail

DATA_DIR="${1:-./data}"
LIMIT_MB="${2:-100}"
THRESHOLD="${3:-85}"

mkdir -p "$DATA_DIR"

current_usage_pct() {
  local size_kb
  size_kb=$(du -sk "$DATA_DIR" | cut -f1)
  local size_mb=$((size_kb / 1024))
  echo $((size_mb * 100 / LIMIT_MB))
}

USAGE=$(current_usage_pct)
echo "$(date '+%Y-%m-%d %H:%M:%S') - Uso simulado de disco en $DATA_DIR: ${USAGE}% (limite ${LIMIT_MB}MB)"

if [ "$USAGE" -ge "$THRESHOLD" ]; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Umbral de ${THRESHOLD}% superado. Iniciando pruning..."

  echo "  -> systemctl stop ethereum-execution   (simulado)"

  # "Pruning": eliminamos los archivos de datos mas antiguos hasta bajar
  # del umbral, igual que 'geth snapshot prune-state' libera espacio.
  for file in "$DATA_DIR"/*.dat; do
    [ -e "$file" ] || continue
    stat -c '%Y %n' "$file"
  done | sort -n | while read -r _ file; do
    NEW_USAGE=$(current_usage_pct)
    [ "$NEW_USAGE" -lt "$THRESHOLD" ] && break
    echo "  -> pruning $file"
    rm -f "$file"
  done

  echo "  -> systemctl start ethereum-execution  (simulado)"
  echo "$(date '+%Y-%m-%d %H:%M:%S') - Pruning completado. Uso final: $(current_usage_pct)%"
else
  echo "$(date '+%Y-%m-%d %H:%M:%S') - No requiere pruning."
fi
