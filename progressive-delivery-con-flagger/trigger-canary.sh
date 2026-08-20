#!/bin/bash
# Dispara un progressive delivery real: cambia la imagen del Deployment
# "podinfo" a una versión nueva y observa cómo Flagger mueve tráfico de
# forma incremental (10% -> 20% -> ... -> 50%) mientras corre el smoke
# test y el load test definidos en canary.yaml, hasta promoverla al 100%
# o revertirla si algo falla.
set -euo pipefail

NAMESPACE="test"
NEW_IMAGE="ghcr.io/stefanprodan/podinfo:6.5.5"

echo "==> Imagen actual de podinfo:"
kubectl get deployment podinfo -n "${NAMESPACE}" \
  -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'

echo "==> Actualizando podinfo a ${NEW_IMAGE} (esto dispara el Canary)..."
kubectl set image deployment/podinfo podinfod="${NEW_IMAGE}" -n "${NAMESPACE}"

echo "==> Siguiendo el progreso del Canary (Ctrl+C para salir)..."
echo "    columnas: STATUS pasa de Progressing a Succeeded (o Failed si"
echo "    Flagger detecta un problema y revierte)."
kubectl get canary podinfo -n "${NAMESPACE}" --watch
