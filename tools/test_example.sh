#!/usr/bin/env bash
# Ejecuta la bateria de pruebas de UN ejemplo y emite un veredicto.
#
# Uso: tools/test_example.sh <directorio-del-ejemplo>
# Salida (ultima linea): RESULT|<dir>|<PASS|PARTIAL|FAIL>|<detalle>
#
# Baterias por tipo (un ejemplo puede acumular varias):
#   - docker-compose.yml  -> up -d, espera, verifica servicios running/healthy, down -v
#   - *.tf                -> tofu init + validate + plan (plan solo si el provider
#                            no exige credenciales cloud reales; si no, PARTIAL)
#   - manifests K8s       -> kubectl apply --dry-run=server contra el cluster actual
#                            (kind en CI); sin cluster disponible -> PARTIAL
#   - *.sh                -> bash -n (los scripts que modifican el sistema NO se
#                            ejecutan: quedan como PARTIAL con razon)
set -uo pipefail

DIR="${1:?uso: test_example.sh <dir>}"
DIR="${DIR%/}"
[ -d "$DIR" ] || { echo "RESULT|$DIR|FAIL|directorio inexistente"; exit 1; }

STATUS="PASS"
NOTES=()

demote() { # degradar el estado global: PASS -> PARTIAL -> FAIL
  local to="$1" why="$2"
  NOTES+=("$why")
  if [ "$to" = "FAIL" ]; then STATUS="FAIL"
  elif [ "$to" = "PARTIAL" ] && [ "$STATUS" = "PASS" ]; then STATUS="PARTIAL"
  fi
}

# ---------- docker compose ----------
while IFS= read -r cf; do
  cdir=$(dirname "$cf")
  echo "== compose: $cf"
  if ! (cd "$cdir" && timeout 600 docker compose up -d --quiet-pull 2>&1 | tail -3); then
    demote FAIL "compose up fallo en $cf"
    (cd "$cdir" && docker compose down -v --remove-orphans >/dev/null 2>&1)
    continue
  fi
  sleep 30
  bad=$(cd "$cdir" && docker compose ps --format '{{.Name}} {{.State}} {{.Health}}' | awk '$2!="running" || ($3!="" && $3!="healthy" && $3!="starting")')
  # dar una segunda oportunidad a los healthchecks lentos
  if [ -n "$bad" ]; then
    sleep 30
    bad=$(cd "$cdir" && docker compose ps --format '{{.Name}} {{.State}} {{.Health}}' | awk '$2!="running" || ($3!="" && $3!="healthy")')
  fi
  if [ -n "$bad" ]; then
    echo "servicios con problemas:"; echo "$bad"
    (cd "$cdir" && docker compose logs --tail 15 2>/dev/null | tail -40)
    demote FAIL "servicios no healthy en $cf: $(echo "$bad" | tr '\n' ';')"
  else
    echo "OK: todos los servicios running/healthy"
  fi
  (cd "$cdir" && docker compose down -v --remove-orphans >/dev/null 2>&1)
done < <(find "$DIR" -name 'docker-compose.yml' -o -name 'compose.yml')

# ---------- terraform / opentofu ----------
while IFS= read -r tdir; do
  echo "== tofu: $tdir"
  # init completo (backends locales son legitimos); si falla (ej. backend remoto), init sin backend
  if ! (cd "$tdir" && tofu init -input=false >/dev/null 2>&1); then
    (cd "$tdir" && tofu init -backend=false -input=false >/dev/null 2>&1)
  fi
  if ! (cd "$tdir" && tofu validate -no-color >/dev/null 2>&1); then
    demote FAIL "tofu validate fallo en $tdir"
    continue
  fi
  # los subdirectorios modules/ no son root modules: validate alcanza
  case "$tdir" in */modules/*|*/module/*) echo "modulo: solo validate"; continue ;; esac
  # plan solo con providers que no exigen credenciales (local, archive, docker con daemon, etc.)
  if grep -rqlE 'provider *"(aws|azurerm|google)"' "$tdir"/*.tf 2>/dev/null; then
    if grep -rql 'localstack\|localhost:4566' "$tdir" 2>/dev/null; then
      # disenado para LocalStack: plan con credenciales dummy
      if (cd "$tdir" && AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 timeout 300 tofu plan -input=false -no-color >/dev/null 2>&1); then
        echo "OK: plan contra LocalStack"
      else
        demote PARTIAL "plan LocalStack fallo en $tdir (validate OK)"
      fi
    else
      demote PARTIAL "requiere credenciales cloud reales: solo validate en $tdir"
    fi
  else
    if (cd "$tdir" && timeout 300 tofu plan -input=false -no-color >/dev/null 2>&1); then
      echo "OK: tofu plan"
    else
      demote FAIL "tofu plan fallo en $tdir"
    fi
  fi
done < <(find "$DIR" -name '*.tf' | xargs -r -n1 dirname | sort -u)

# ---------- manifests kubernetes ----------
K8S_FILES=$(grep -rlE '^kind:' "$DIR" --include='*.yaml' --include='*.yml' 2>/dev/null | grep -vE 'templates/|Chart.yaml|docker-compose|compose.yml|values' || true)
if [ -n "$K8S_FILES" ]; then
  if kubectl cluster-info >/dev/null 2>&1; then
    while IFS= read -r kf; do
      echo "== k8s dry-run: $kf"
      out=$(kubectl apply --dry-run=server -f "$kf" 2>&1)
      if [ $? -ne 0 ]; then
        # CRDs de operadores no instalados son PARTIAL, no FAIL
        if echo "$out" | grep -qiE 'no matches for kind|ensure CRDs are installed'; then
          demote PARTIAL "requiere CRDs/operador no instalado: $kf"
        else
          echo "$out" | head -5
          demote FAIL "dry-run fallo: $kf"
        fi
      fi
    done <<< "$K8S_FILES"
  else
    demote PARTIAL "manifests K8s sin cluster disponible para dry-run"
  fi
fi

# ---------- helm ----------
while IFS= read -r ch; do
  chdir=$(dirname "$ch")
  echo "== helm: $chdir"
  helm lint "$chdir" >/dev/null 2>&1 && helm template "$chdir" >/dev/null 2>&1 || demote FAIL "helm lint/template fallo en $chdir"
done < <(find "$DIR" -name Chart.yaml)

# ---------- scripts ----------
while IFS= read -r sh; do
  bash -n "$sh" 2>/dev/null || demote FAIL "sintaxis bash invalida: $sh"
done < <(find "$DIR" -name '*.sh')
# los scripts que tocan el sistema no se ejecutan
if grep -rlqE '^\s*(sysctl -w|iptables|ufw |firewall-cmd|modprobe|mount |useradd|systemctl (start|enable))' "$DIR" --include='*.sh' 2>/dev/null; then
  demote PARTIAL "contiene scripts que modifican el sistema: no se ejecutan automaticamente"
fi
while IFS= read -r py; do
  python3 -m py_compile "$py" 2>/dev/null || demote FAIL "sintaxis python invalida: $py"
done < <(find "$DIR" -name '*.py')

DETAIL=$(IFS='; '; echo "${NOTES[*]:-ok}")
echo "RESULT|$DIR|$STATUS|$DETAIL"
[ "$STATUS" = "FAIL" ] && exit 1 || exit 0
