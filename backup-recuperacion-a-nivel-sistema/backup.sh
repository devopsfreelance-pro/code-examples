#!/bin/bash
# Backup completo de la base de datos "appdb" con dump comprimido y
# encriptado con GPG (simétrico), replicando el patrón del post:
# full backup + encriptación + verificación de checksum.

set -euo pipefail

CONTAINER_NAME="br-postgres"
DB_USER="appuser"
DB_NAME="appdb"
BACKUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/backups"
BACKUP_PASSPHRASE="${BACKUP_PASSPHRASE:-cambiar-esta-passphrase}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

mkdir -p "${BACKUP_DIR}"

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log "ERROR: el contenedor ${CONTAINER_NAME} no está corriendo. Ejecuta 'docker compose up -d' primero."
    exit 1
fi

backup_date="$(date +%Y%m%d_%H%M%S)"
dump_file="${BACKUP_DIR}/appdb_${backup_date}.sql.gz"
encrypted_file="${dump_file}.gpg"

log "Generando dump de ${DB_NAME}..."
docker exec "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" --clean --if-exists "${DB_NAME}" \
    | gzip > "${dump_file}"

log "Encriptando backup con GPG (AES256)..."
gpg --batch --yes --cipher-algo AES256 --symmetric \
    --passphrase "${BACKUP_PASSPHRASE}" \
    --output "${encrypted_file}" "${dump_file}"

rm -f "${dump_file}"

checksum="$(sha256sum "${encrypted_file}" | cut -d' ' -f1)"

log "Backup completado: ${encrypted_file}"
log "Checksum SHA256: ${checksum}"
log "Tamaño: $(du -h "${encrypted_file}" | cut -f1)"

# Retención simple: conservar solo los últimos 5 backups locales
ls -1t "${BACKUP_DIR}"/*.gpg 2>/dev/null | tail -n +6 | xargs -r rm -f
