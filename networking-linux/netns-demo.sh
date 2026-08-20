#!/usr/bin/env bash
# Demuestra el concepto central del post: dos network namespaces conectados
# por un par veth, exactamente lo que hace Docker/CNI de Kubernetes por
# debajo cada vez que levanta un contenedor con red bridge.
set -euo pipefail

NS=mi_namespace
VETH_HOST=veth0
VETH_NS=veth1
IP_HOST=10.0.0.2/24
IP_NS=10.0.0.1/24

echo "== 1. Crear el namespace =="
ip netns add "$NS"

echo "== 2. Crear el par veth (dos interfaces virtuales unidas entre si) =="
ip link add "$VETH_HOST" type veth peer name "$VETH_NS"

echo "== 3. Mover un extremo del par al namespace =="
ip link set "$VETH_NS" netns "$NS"

echo "== 4. Configurar IP y levantar el extremo dentro del namespace =="
ip netns exec "$NS" ip addr add "$IP_NS" dev "$VETH_NS"
ip netns exec "$NS" ip link set "$VETH_NS" up
ip netns exec "$NS" ip link set lo up

echo "== 5. Configurar IP y levantar el extremo en el host (namespace por defecto) =="
ip addr add "$IP_HOST" dev "$VETH_HOST"
ip link set "$VETH_HOST" up

echo
echo "== 6. Verificar conectividad en ambas direcciones =="
echo "--- host -> namespace ---"
ping -c 3 "${IP_NS%/*}"
echo "--- namespace -> host ---"
ip netns exec "$NS" ping -c 3 "${IP_HOST%/*}"

echo
echo "== 7. Interfaces y namespaces resultantes =="
echo "--- namespaces ---"
ip netns list
echo "--- interfaz en el host ---"
ip -brief addr show "$VETH_HOST"
echo "--- interfaz dentro del namespace ---"
ip netns exec "$NS" ip -brief addr show "$VETH_NS"

echo
echo "Listo. Corre ./cleanup.sh para eliminar el namespace y el par veth."
