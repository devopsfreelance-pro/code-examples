#!/usr/bin/env bash
# Mini-SAST: busca credenciales hardcodeadas en el codigo fuente, ilustrando
# el Requisito 2 (sin valores predeterminados/hardcodeados) y el Requisito
# 6.2 (revision de codigo orientada a seguridad) de PCI DSS.
#
# Uso: ./scan_hardcoded_creds.sh [directorio]
# Exit code 0 = limpio, 1 = se encontraron posibles secretos.

set -euo pipefail

TARGET_DIR="${1:-.}"
FOUND=0

# Patrones tipicos de credenciales hardcodeadas.
PATTERNS=(
    'password\s*=\s*["'\''][^"'\'' ]{3,}["'\'']'
    'passwd\s*=\s*["'\''][^"'\'' ]{3,}["'\'']'
    'secret\s*=\s*["'\''][^"'\'' ]{3,}["'\'']'
    'api[_-]?key\s*=\s*["'\''][^"'\'' ]{6,}["'\'']'
    'AKIA[0-9A-Z]{16}'
    'BEGIN (RSA|EC|OPENSSH) PRIVATE KEY'
)

echo "Escaneando '${TARGET_DIR}' en busca de credenciales hardcodeadas..."

for pattern in "${PATTERNS[@]}"; do
    matches=$(grep -rInE \
        --exclude-dir=".git" \
        --exclude-dir="secrets" \
        --exclude="scan_hardcoded_creds.sh" \
        --exclude="*.txt" \
        -e "$pattern" \
        "$TARGET_DIR" 2>/dev/null || true)

    if [[ -n "$matches" ]]; then
        echo "--- posible credencial hardcodeada (patron: $pattern) ---"
        echo "$matches"
        FOUND=1
    fi
done

if [[ "$FOUND" -eq 1 ]]; then
    echo
    echo "RESULTADO: se encontraron posibles credenciales hardcodeadas."
    exit 1
fi

echo "RESULTADO: sin coincidencias. OK."
exit 0
