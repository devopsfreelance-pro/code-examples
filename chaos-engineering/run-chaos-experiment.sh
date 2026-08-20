#!/usr/bin/env bash
#
# run-chaos-experiment.sh
#
# Implementa, con kubectl puro, el experimento de ejemplo del post:
#
#   hipótesis: "el servicio de checkout mantiene disponibilidad >99.9%
#               con 2 de 5 pods terminados"
#   método:    pod-termination, 2 pods, cada 15s
#   rollback:  si la disponibilidad cae por debajo del 95%, se detiene
#              el experimento (equivalente al "condition / action" del
#              YAML del post)
#
# Requisitos: kind, kubectl, curl, shuf (coreutils), bc
#
set -euo pipefail

NAMESPACE="chaos-demo"
APP_LABEL="app=checkout-service"
LOCAL_PORT=8080
PODS_TO_KILL=2
KILL_INTERVAL=15          # segundos entre cada tanda de terminaciones
EXPERIMENT_DURATION=60    # duración total del experimento en segundos
ROLLBACK_THRESHOLD=95     # % de disponibilidad, por debajo se aborta
HYPOTHESIS_THRESHOLD=99.9 # % de disponibilidad objetivo (steady-state)

LOG_FILE="$(mktemp)"
PF_PID=""

cleanup() {
  echo ""
  echo "Limpiando: deteniendo port-forward y monitor..."
  [[ -n "${MONITOR_PID:-}" ]] && kill "${MONITOR_PID}" 2>/dev/null || true
  [[ -n "${PF_PID:-}" ]] && kill "${PF_PID}" 2>/dev/null || true
  rm -f "${LOG_FILE}"
}
trap cleanup EXIT

echo "== Chaos Engineering demo: pod-termination-checkout-service =="
echo ""
echo "Hipótesis: checkout-service mantiene disponibilidad >${HYPOTHESIS_THRESHOLD}% con ${PODS_TO_KILL} de 5 pods terminados"
echo ""

echo "1) Aplicando manifiestos (namespace + deployment + service)..."
kubectl apply -f "$(dirname "$0")/k8s/checkout-service.yaml"

echo ""
echo "2) Esperando steady-state inicial (rollout de 5 réplicas listas)..."
kubectl -n "${NAMESPACE}" rollout status deployment/checkout-service --timeout=120s

echo ""
echo "3) Abriendo port-forward hacia el servicio (localhost:${LOCAL_PORT})..."
kubectl -n "${NAMESPACE}" port-forward svc/checkout-service "${LOCAL_PORT}:80" >/dev/null 2>&1 &
PF_PID=$!

# Esperar a que el port-forward esté listo
for i in $(seq 1 20); do
  if curl -s -o /dev/null "http://localhost:${LOCAL_PORT}"; then
    break
  fi
  sleep 0.5
done

echo ""
echo "4) Iniciando monitor de disponibilidad (1 request/seg, log en ${LOG_FILE})..."
(
  while true; do
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "http://localhost:${LOCAL_PORT}" || echo "000")
    if [[ "${code}" == "200" ]]; then
      echo "1" >> "${LOG_FILE}"
    else
      echo "0" >> "${LOG_FILE}"
    fi
    sleep 1
  done
) &
MONITOR_PID=$!

availability_now() {
  local total success
  total=$(wc -l < "${LOG_FILE}" 2>/dev/null || echo 0)
  if [[ "${total}" -eq 0 ]]; then
    echo "100.0"
    return
  fi
  success=$(grep -c '^1$' "${LOG_FILE}" || true)
  echo "scale=2; ${success} * 100 / ${total}" | bc
}

echo ""
echo "5) Método: terminando ${PODS_TO_KILL} pods cada ${KILL_INTERVAL}s durante ${EXPERIMENT_DURATION}s..."
echo ""

elapsed=0
rollback_triggered=false

while [[ ${elapsed} -lt ${EXPERIMENT_DURATION} ]]; do
  sleep "${KILL_INTERVAL}"
  elapsed=$((elapsed + KILL_INTERVAL))

  victims=$(kubectl -n "${NAMESPACE}" get pods -l "${APP_LABEL}" -o name | shuf -n "${PODS_TO_KILL}")
  echo ">> t=${elapsed}s: terminando pods:"
  echo "${victims}" | sed 's/^/     /'
  # shellcheck disable=SC2086
  kubectl -n "${NAMESPACE}" delete ${victims} --wait=false >/dev/null

  avail=$(availability_now)
  echo "   disponibilidad acumulada: ${avail}%"

  if (( $(echo "${avail} < ${ROLLBACK_THRESHOLD}" | bc -l) )); then
    echo ""
    echo "!! ROLLBACK: disponibilidad ${avail}% < ${ROLLBACK_THRESHOLD}% -> deteniendo experimento"
    rollback_triggered=true
    break
  fi
done

kill "${MONITOR_PID}" 2>/dev/null || true
wait "${MONITOR_PID}" 2>/dev/null || true

final_availability=$(availability_now)

echo ""
echo "== Resultado del experimento =="
echo "Disponibilidad medida: ${final_availability}%"

if [[ "${rollback_triggered}" == "true" ]]; then
  echo "Estado: ABORTADO por rollback (condición de seguridad activada)"
  echo "Hipótesis: RECHAZADA — el sistema no toleró la pérdida de ${PODS_TO_KILL} pods sin degradarse"
elif (( $(echo "${final_availability} >= ${HYPOTHESIS_THRESHOLD}" | bc -l) )); then
  echo "Estado: completado"
  echo "Hipótesis: CONFIRMADA — disponibilidad >= ${HYPOTHESIS_THRESHOLD}% con pods terminados"
else
  echo "Estado: completado"
  echo "Hipótesis: RECHAZADA — disponibilidad ${final_availability}% por debajo del objetivo ${HYPOTHESIS_THRESHOLD}%"
fi

kubectl -n "${NAMESPACE}" get pods -l "${APP_LABEL}"
