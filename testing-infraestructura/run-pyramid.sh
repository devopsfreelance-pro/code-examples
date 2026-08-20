#!/usr/bin/env bash
# Recorre los primeros tres niveles de la pirámide de testing de IaC
# (validate -> lint -> plan + policy) descritos en el post, y opcionalmente
# el cuarto nivel (integración: apply + destroy contra LocalStack).
#
# Uso:
#   ./run-pyramid.sh            # niveles 1-3 (validate, tflint, plan+policy)
#   ./run-pyramid.sh --apply    # además aplica y destruye contra LocalStack
#   ./run-pyramid.sh --break    # fuerza enable_encryption=false para ver
#                                # a conftest bloquear el plan

set -euo pipefail

# Credenciales dummy: LocalStack no valida credenciales reales, pero el
# CLI de AWS exige que existan para no fallar con "Unable to locate credentials".
export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-test}"
export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-test}"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="$SCRIPT_DIR/terraform"
POLICY_DIR="$SCRIPT_DIR/policy"

DO_APPLY=false
TF_VAR_ARGS=()

for arg in "$@"; do
  case "$arg" in
    --apply) DO_APPLY=true ;;
    --break) TF_VAR_ARGS+=("-var=enable_encryption=false") ;;
    *)
      echo "Argumento desconocido: $arg" >&2
      exit 1
      ;;
  esac
done

echo "== Nivel 1: validación estática y linting =="
terraform -chdir="$TF_DIR" init -input=false -upgrade=false >/dev/null
terraform -chdir="$TF_DIR" fmt -check -diff
terraform -chdir="$TF_DIR" validate

if command -v tflint >/dev/null 2>&1; then
  (cd "$TF_DIR" && tflint --init >/dev/null 2>&1 || true)
  (cd "$TF_DIR" && tflint)
else
  echo "tflint no está instalado, se omite (ver README para instalarlo)"
fi

echo
echo "== Nivel 2: plan =="
terraform -chdir="$TF_DIR" plan -input=false -out=tfplan "${TF_VAR_ARGS[@]}"

echo
echo "== Nivel 3: policy as code sobre el plan =="
if command -v conftest >/dev/null 2>&1; then
  terraform -chdir="$TF_DIR" show -json tfplan | conftest test -p "$POLICY_DIR" -
else
  echo "conftest no está instalado, se omite (ver README para instalarlo)"
fi

if [ "$DO_APPLY" = true ]; then
  echo
  echo "== Nivel 4: integración real contra LocalStack (apply + destroy) =="
  trap 'terraform -chdir="$TF_DIR" destroy -input=false -auto-approve "${TF_VAR_ARGS[@]}"' EXIT
  terraform -chdir="$TF_DIR" apply -input=false tfplan
  BUCKET=$(terraform -chdir="$TF_DIR" output -raw bucket_id)
  echo "Verificando que el bucket existe en LocalStack..."
  aws --endpoint-url=http://localhost:4566 s3api head-bucket --bucket "$BUCKET"
  echo "OK: bucket '$BUCKET' confirmado en LocalStack. Destruyendo..."
fi

rm -f "$TF_DIR/tfplan"
echo
echo "Listo."
