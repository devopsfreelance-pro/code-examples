#!/usr/bin/env bash
# Demo de Kubernetes HPA (Horizontal Pod Autoscaler) sobre un cluster kind local.
#
# Crea un cluster kind, instala metrics-server (parcheado para funcionar sin
# TLS valido, como requiere kind), despliega la app de ejemplo php-apache,
# aplica el HPA y genera carga para disparar el autoscaling en vivo.
set -euo pipefail

CLUSTER_NAME="hpa-demo"

echo "==> 1. Creando cluster kind '${CLUSTER_NAME}' (si no existe)"
if ! kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
  kind create cluster --name "${CLUSTER_NAME}"
else
  echo "    Cluster '${CLUSTER_NAME}' ya existe, se reutiliza."
fi
kubectl config use-context "kind-${CLUSTER_NAME}"

echo "==> 2. Instalando metrics-server"
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

echo "==> 3. Parcheando metrics-server para aceptar TLS de kubelet en kind"
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[
  {"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}
]' || true

echo "==> 4. Esperando a que metrics-server este listo"
kubectl rollout status deployment/metrics-server -n kube-system --timeout=120s

echo "==> 5. Desplegando app de ejemplo (php-apache) y su Service"
kubectl apply -f deployment.yaml
kubectl rollout status deployment/php-apache --timeout=120s

echo "==> 6. Aplicando el HorizontalPodAutoscaler"
kubectl apply -f hpa.yaml

echo "==> 7. Esperando a que 'kubectl top pods' devuelva metricas reales (puede tardar ~1 min)"
for i in $(seq 1 20); do
  if kubectl top pods -l app=php-apache >/dev/null 2>&1; then
    break
  fi
  sleep 5
done

echo "==> 8. Lanzando el generador de carga (busybox en loop contra el Service)"
kubectl delete pod load-generator --ignore-not-found
kubectl apply -f load-generator.yaml

cat <<'EOF'

==> Listo. Ahora observa el HPA escalar en tiempo real con:

    kubectl get hpa php-apache-hpa --watch

En 1-2 minutos deberias ver como REPLICAS sube de 1 a varios pods cuando
TARGETS (CPU actual/objetivo) supera el 50% configurado en hpa.yaml.

Para cortar la carga y ver el scale-down (tarda ~1 min por el
stabilizationWindowSeconds del behavior):

    kubectl delete pod load-generator

Para destruir todo el cluster de la demo:

    kind delete cluster --name hpa-demo
EOF
