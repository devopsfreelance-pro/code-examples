#!/bin/bash
# Recuperación (disaster recovery) a partir del backup encriptado más
# reciente: desencripta, descomprime y restaura sobre la base de datos.
# Uso: ./restore.sh [ruta_al_archivo.gpg]

set -euo pipefail

CONTAINER_NAME="br-postgres"
DB_USER="appuser"
DB_NAME="appdb"
BACKUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/backups"
BACKUP_PASSPHRASE="${BACKUP_PASSPHRASE:-cambiar-esta-passphrase}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log "ERROR: el contenedor ${CONTAINER_NAME} no está corriendo. Ejecuta 'docker compose up -d' primero."
    exit 1
fi

encrypted_file="${1:-}"
if [ -z "${encrypted_file}" ]; then
    encrypted_file="$(ls -1t "${BACKUP_DIR}"/*.gpg 2>/dev/null | head -n1)"
fi

if [ -z "${encrypted_file}" ] || [ ! -f "${encrypted_file}" ]; then
    log "ERROR: no se encontró ningún backup en ${BACKUP_DIR}. Ejecuta ./backup.sh primero."
    exit 1
fi

log "Restaurando desde: ${encrypted_file}"

tmp_dump="$(mktemp /tmp/appdb_restore_XXXXXX.sql.gz)"
trap 'rm -f "${tmp_dump}"' EXIT

log "Desencriptando backup..."
gpg --batch --yes --decrypt \
    --passphrase "${BACKUP_PASSPHRASE}" \
    --output "${tmp_dump}" "${encrypted_file}"

log "Restaurando datos en ${DB_NAME}..."
gunzip -c "${tmp_dump}" | docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}"

log "Restauración completada."
log "Verificando datos restaurados..."
docker exec "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT count(*) AS pedidos_restaurados FROM pedidos;"
