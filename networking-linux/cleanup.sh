#!/usr/bin/env bash
# Elimina el namespace y el par veth creados por netns-demo.sh.
# Idempotente: no falla si los recursos ya no existen.
set -uo pipefail

NS=mi_namespace
VETH_HOST=veth0

ip netns del "$NS" 2>/dev/null && echo "namespace $NS eliminado" || echo "namespace $NS no existia"
ip link del "$VETH_HOST" 2>/dev/null && echo "interfaz $VETH_HOST eliminada" || echo "interfaz $VETH_HOST no existia"

echo "Cleanup terminado."
