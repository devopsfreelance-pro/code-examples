#!/usr/bin/env bash
# Verifica en vivo las prácticas del post: probes, resource requests/limits,
# PodDisruptionBudget y NetworkPolicy sobre el Deployment ya desplegado.
set -euo pipefail

NS="production"

echo "=== 1) Requests/limits efectivos (LimitRange + Deployment) ==="
kubectl get pods -n "${NS}" -l app=api-demo \
  -o custom-columns='POD:.metadata.name,CPU-REQ:.spec.containers[0].resources.requests.cpu,MEM-REQ:.spec.containers[0].resources.requests.memory,CPU-LIM:.spec.containers[0].resources.limits.cpu,MEM-LIM:.spec.containers[0].resources.limits.memory'

echo
echo "=== 2) Probes configuradas (liveness/readiness/startup) ==="
kubectl get pods -n "${NS}" -l app=api-demo -o jsonpath='{range .items[*]}{.metadata.name}{"\n  liveness: "}{.spec.containers[0].livenessProbe.httpGet.path}{"\n  readiness: "}{.spec.containers[0].readinessProbe.httpGet.path}{"\n  startup: "}{.spec.containers[0].startupProbe.httpGet.path}{"\n"}{end}'

echo
echo "=== 3) PodDisruptionBudget: cuántos pods se pueden desalojar a la vez ==="
kubectl get pdb api-demo-pdb -n "${NS}"

echo
echo "=== 4) HPA: réplicas actuales vs uso de CPU (puede tardar ~1 min en poblarse) ==="
kubectl get hpa api-demo-hpa -n "${NS}"

echo
echo "=== 5) NetworkPolicy: sin label role=client, el acceso debe fallar (timeout esperado) ==="
kubectl run cliente-no-autorizado -n "${NS}" --rm -i --restart=Never \
  --image=busybox:1.36 --command -- wget -q -T 5 -O- http://api-demo.production.svc.cluster.local \
  || echo "OK: bloqueado por NetworkPolicy (o CNI sin soporte de enforcement, ver README)"

echo
echo "=== 6) Con label role=client, el acceso debe funcionar ==="
kubectl run cliente-autorizado -n "${NS}" --rm -i --restart=Never \
  --labels="role=client" \
  --image=busybox:1.36 --command -- wget -q -T 5 -O- http://api-demo.production.svc.cluster.local \
  && echo "OK: acceso permitido"
