#!/usr/bin/env bash
# Genera "evidencia de auditoria" SOC2 automatizada: corre terraform plan,
# evalua el plan contra la politica OPA (policy/soc2_controls.rego) y deja
# un archivo evidence-<timestamp>.json con el resultado. Pensado para
# correr en un pipeline de CI/CD como el descripto en el post (validacion
# de politicas antes de cada despliegue).
set -euo pipefail
cd "$(dirname "$0")"

export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-test}"
export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-test}"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

echo "==> terraform init"
terraform init -input=false -no-color

echo "==> terraform plan"
terraform plan -input=false -no-color -out=tfplan

echo "==> terraform show -json"
terraform show -json tfplan > tfplan.json

if command -v opa >/dev/null 2>&1; then
  OPA_EVAL=(opa eval)
else
  echo "==> opa no esta instalado localmente, usando la imagen Docker openpolicyagent/opa"
  OPA_EVAL=(docker run --rm -v "$(pwd):/workspace" -w /workspace openpolicyagent/opa eval)
fi

echo "==> Evaluando controles SOC2 (cifrado, acceso publico, versionado) con OPA"
RESULT_JSON=$("${OPA_EVAL[@]}" --format json \
  --data policy/soc2_controls.rego \
  --input tfplan.json \
  "data.soc2.controls.deny" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(json.dumps(d["result"][0]["expressions"][0]["value"]))')

TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EVIDENCE_FILE="evidence-${TIMESTAMP//:/-}.json"

if [ "$RESULT_JSON" = "[]" ]; then
  STATUS="PASS"
else
  STATUS="FAIL"
fi

cat > "$EVIDENCE_FILE" <<EOF
{
  "control": "CC6.1 - Logical Access / Confidentiality (cifrado, acceso publico y versionado en buckets S3)",
  "timestamp": "${TIMESTAMP}",
  "status": "${STATUS}",
  "tool": "opa eval sobre terraform plan (policy as code)",
  "findings": ${RESULT_JSON}
}
EOF

echo ""
echo "Evidencia generada: ${EVIDENCE_FILE} (status: ${STATUS})"
cat "$EVIDENCE_FILE"

if [ "$STATUS" = "FAIL" ]; then
  echo ""
  echo "Este es el resultado esperado: el bucket 'soc2-demo-noncompliant-bucket' no cumple los 3 controles."
  exit 1
fi
