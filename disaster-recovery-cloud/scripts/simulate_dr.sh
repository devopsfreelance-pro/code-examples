#!/usr/bin/env bash
#
# simulate_dr.sh
#
# Simula un ciclo completo de Disaster Recovery en cloud (nivel "Backup y
# Restore" / "Pilot Light") usando LocalStack como stand-in de dos regiones
# de AWS: bucket "primario" (region activa) y bucket "dr" (region de
# recuperacion). Mide RTO y RPO reales del propio ejercicio.
#
# Requiere: docker compose levantado (ver README) y AWS CLI v2 instalado.
set -euo pipefail

ENDPOINT="http://localhost:4566"
REGION="us-east-1"
PRIMARY_BUCKET="app-datos-primario"
DR_BUCKET="app-datos-dr"
RESTORED_BUCKET="app-datos-restaurado"
WORKDIR="$(mktemp -d)"

export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="$REGION"

aws_local() {
  aws --endpoint-url="$ENDPOINT" --region "$REGION" "$@"
}

log() {
  echo "[$(date '+%H:%M:%S')] $*"
}

wait_for_localstack() {
  log "Esperando a que LocalStack este listo..."
  for _ in $(seq 1 30); do
    if curl -sf "${ENDPOINT}/_localstack/health" >/dev/null 2>&1; then
      log "LocalStack listo."
      return 0
    fi
    sleep 2
  done
  echo "ERROR: LocalStack no respondio a tiempo." >&2
  exit 1
}

setup_buckets() {
  log "Creando buckets (simulando region primaria y region DR)..."
  aws_local s3 mb "s3://${PRIMARY_BUCKET}" >/dev/null
  aws_local s3 mb "s3://${DR_BUCKET}" >/dev/null
  aws_local s3api put-bucket-versioning \
    --bucket "$PRIMARY_BUCKET" --versioning-configuration Status=Enabled >/dev/null
  aws_local s3api put-bucket-versioning \
    --bucket "$DR_BUCKET" --versioning-configuration Status=Enabled >/dev/null
  log "Buckets creados: ${PRIMARY_BUCKET} (primario), ${DR_BUCKET} (DR)."
}

write_sample_data() {
  local filename="$1"
  local content="$2"
  echo "$content" > "${WORKDIR}/${filename}"
  aws_local s3 cp "${WORKDIR}/${filename}" "s3://${PRIMARY_BUCKET}/${filename}" >/dev/null
  log "Dato critico escrito en primario: ${filename}"
}

replicate_to_dr() {
  log "Replicando primario -> DR (equivalente a S3 Cross-Region Replication)..."
  aws_local s3 sync "s3://${PRIMARY_BUCKET}" "s3://${DR_BUCKET}" --delete >/dev/null
  REPLICATION_TS=$(date +%s)
  log "Replicacion completada. Checkpoint RPO: $(date -d @${REPLICATION_TS} '+%H:%M:%S')"
}

purge_versioned_bucket() {
  # Los buckets con versioning no se vacian con "s3 rm" ni "s3 rb --force":
  # hay que borrar cada version y cada delete-marker explicitamente.
  local bucket="$1"
  local versions
  versions=$(aws_local s3api list-object-versions --bucket "$bucket" \
    --output json --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}')
  if [ "$(echo "$versions" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d.get("Objects") or []))')" != "0" ]; then
    aws_local s3api delete-objects --bucket "$bucket" --delete "$versions" >/dev/null
  fi
  local markers
  markers=$(aws_local s3api list-object-versions --bucket "$bucket" \
    --output json --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}')
  if [ "$(echo "$markers" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d.get("Objects") or []))')" != "0" ]; then
    aws_local s3api delete-objects --bucket "$bucket" --delete "$markers" >/dev/null
  fi
}

simulate_disaster() {
  log "=== SIMULANDO DESASTRE: perdida de la region primaria ==="
  purge_versioned_bucket "$PRIMARY_BUCKET"
  aws_local s3 rb "s3://${PRIMARY_BUCKET}" --force >/dev/null
  DISASTER_TS=$(date +%s)
  log "Region primaria eliminada en $(date -d @${DISASTER_TS} '+%H:%M:%S')."
}

failover() {
  log "=== INICIANDO FAILOVER hacia la region DR ==="
  FAILOVER_START=$(date +%s)

  aws_local s3 mb "s3://${RESTORED_BUCKET}" >/dev/null
  aws_local s3 sync "s3://${DR_BUCKET}" "s3://${RESTORED_BUCKET}" >/dev/null

  FAILOVER_END=$(date +%s)
  log "Failover completado en $(date -d @${FAILOVER_END} '+%H:%M:%S')."
}

report() {
  local rto=$((FAILOVER_END - FAILOVER_START))
  local rpo=$((DISASTER_TS - REPLICATION_TS))

  echo ""
  echo "================= REPORTE DE DISASTER RECOVERY ================="
  echo "Bucket restaurado: s3://${RESTORED_BUCKET}"
  echo "Objetos recuperados:"
  aws_local s3 ls "s3://${RESTORED_BUCKET}" --recursive | awk '{print "  - "$NF}'
  echo ""
  echo "RTO (tiempo de recuperacion, failover completo): ${rto}s"
  echo "RPO (ventana de datos potencialmente perdidos):  ${rpo}s"
  echo "==================================================================="
}

cleanup_previous_run() {
  for bucket in "$PRIMARY_BUCKET" "$DR_BUCKET" "$RESTORED_BUCKET"; do
    if aws_local s3api head-bucket --bucket "$bucket" >/dev/null 2>&1; then
      purge_versioned_bucket "$bucket" || true
      aws_local s3 rb "s3://${bucket}" --force >/dev/null 2>&1 || true
    fi
  done
}

main() {
  wait_for_localstack
  cleanup_previous_run

  setup_buckets
  write_sample_data "clientes.json" '{"id": 1, "nombre": "cliente-critico", "saldo": 15000}'
  write_sample_data "transacciones.log" "2026-02-04T10:00:00Z transaccion-001 OK"

  replicate_to_dr

  # Escritura posterior al ultimo checkpoint de replicacion: representa
  # datos que se perderian con este RPO si el desastre ocurre ahora.
  write_sample_data "transacciones.log" "2026-02-04T10:00:00Z transaccion-001 OK
2026-02-04T10:05:00Z transaccion-002 OK (no replicada aun)"

  simulate_disaster
  failover
  report

  rm -rf "$WORKDIR"
}

main "$@"
