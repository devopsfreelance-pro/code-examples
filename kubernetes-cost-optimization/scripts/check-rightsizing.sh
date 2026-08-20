#!/usr/bin/env bash
# Compara requests declarados vs consumo real (kubectl top) para detectar
# sobreaprovisionamiento, el mismo chequeo que el post hace con PromQL
# (container_cpu_usage_seconds_total / kube_pod_container_resource_requests)
# pero usando metrics-server via kubectl, sin necesidad de Prometheus.
set -euo pipefail

NAMESPACE="cost-demo"

echo "=== Requests declarados (resources.requests) ==="
kubectl get pods -n "${NAMESPACE}" -o json |
  python3 -c '
import json, sys
data = json.load(sys.stdin)
for pod in data["items"]:
    name = pod["metadata"]["name"]
    for c in pod["spec"]["containers"]:
        req = c.get("resources", {}).get("requests", {})
        cpu_req = req.get("cpu", "n/a")
        mem_req = req.get("memory", "n/a")
        print(f"{name}\tcpu_request={cpu_req}\tmem_request={mem_req}")
'

echo ""
echo "=== Esperando metricas reales de metrics-server (puede tardar ~30-60s) ==="
for i in $(seq 1 15); do
  if kubectl top pods -n "${NAMESPACE}" >/dev/null 2>&1; then
    break
  fi
  echo "  metricas todavia no disponibles, reintentando ($i/15)..."
  sleep 5
done

echo ""
echo "=== Uso real (kubectl top pods) ==="
kubectl top pods -n "${NAMESPACE}"

echo ""
echo "=== Conclusion ==="
echo "Compara CPU(cores)/MEMORY(bytes) de 'kubectl top' contra los requests de"
echo "arriba: si el uso real esta muy por debajo del request (ratio < 0.5, la"
echo "regla del post), el Deployment esta sobredimensionado. En este demo,"
echo "api-catalogo pide 1 CPU / 1Gi por pod pero nginxdemos/hello en reposo usa"
echo "apenas unos mCPU y ~10-20Mi: es exactamente el caso que 'Right-sizing'"
echo "describe en el post."
