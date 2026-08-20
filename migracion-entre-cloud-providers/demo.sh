#!/usr/bin/env bash
# Demo del post "Migración entre cloud providers": migración de datos
# entre dos proveedores con Rclone (sincronización inicial + incremental
# con verificación), tal como describe la sección "Herramientas de
# migración de datos" del post.
#
# Usamos dos MinIO locales (compatibles con la API S3) para representar
# el bucket de origen (AWS S3) y el contenedor de destino (Azure Blob).
# No requiere cuentas ni credenciales de un cloud real.

set -euo pipefail

COMPOSE="docker compose"
BUCKET=app-data

cleanup() {
  echo
  echo "==> Apagando el entorno (docker compose down -v)"
  $COMPOSE down -v >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "==> Levantando MinIO origen (simula AWS S3) y destino (simula Azure Blob)"
$COMPOSE up -d origin destination rclone

echo "==> Esperando a que ambos MinIO estén healthy"
for svc in origin destination; do
  until [ "$($COMPOSE ps -q "$svc" | xargs docker inspect -f '{{.State.Health.Status}}')" = "healthy" ]; do
    sleep 1
  done
done

echo "==> Creando bucket '$BUCKET' en el proveedor de origen"
docker exec cloudmig-rclone rclone mkdir "aws-origin:${BUCKET}"

echo "==> Generando datos de ejemplo y subiéndolos al origen"
docker exec cloudmig-rclone sh -c "
  mkdir -p /tmp/seed &&
  echo 'reporte de ventas Q1' > /tmp/seed/ventas-q1.txt &&
  echo 'reporte de ventas Q2' > /tmp/seed/ventas-q2.txt &&
  dd if=/dev/urandom of=/tmp/seed/binario.bin bs=1024 count=256 status=none
"
docker exec cloudmig-rclone rclone copy /tmp/seed "aws-origin:${BUCKET}" --progress

echo
echo "==> Sincronización inicial: origen -> destino (equivalente al post)"
docker exec cloudmig-rclone rclone sync \
  "aws-origin:${BUCKET}" "azure-destination:${BUCKET}" \
  --progress --checksum

echo
echo "==> Verificación de integridad tras la migración (rclone check)"
docker exec cloudmig-rclone rclone check \
  "aws-origin:${BUCKET}" "azure-destination:${BUCKET}"

echo
echo "==> Simulando escritura nueva en el origen mientras el sistema sigue en uso"
docker exec cloudmig-rclone sh -c "
  echo 'reporte de ventas Q3 (nuevo, post-corte)' > /tmp/seed/ventas-q3.txt
"
docker exec cloudmig-rclone rclone copy /tmp/seed "aws-origin:${BUCKET}" --progress

echo
echo "==> Sincronización incremental para minimizar downtime (solo lo nuevo/cambiado)"
docker exec cloudmig-rclone rclone sync \
  "aws-origin:${BUCKET}" "azure-destination:${BUCKET}" \
  --progress --checksum

echo
echo "==> Listado final en destino (debe incluir ventas-q3.txt)"
docker exec cloudmig-rclone rclone ls "azure-destination:${BUCKET}"

echo
echo "==> Migración completa y verificada. El origen y el destino están en paridad."
