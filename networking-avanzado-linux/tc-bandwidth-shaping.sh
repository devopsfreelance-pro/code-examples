#!/usr/bin/env bash
# Demuestra "Traffic Control (tc) y QoS" del post: mide con una transferencia
# real el throughput entre dos network namespaces conectados por un par veth,
# primero sin limite y despues con un qdisc htb que limita el trafico
# saliente a 1mbit, para comprobar que tc realmente reduce el ancho de banda
# al valor configurado.
set -euo pipefail

NS=shaped-ns
VETH_HOST=veth-host
VETH_NS=veth-ns
IP_HOST=10.20.0.1/24
IP_NS=10.20.0.2/24
PORT=5001
FILE=/tmp/tc-test-payload.bin
FILE_SIZE_MB=5
RATE=1mbit

cleanup_transfer() {
    ip netns exec "$NS" pkill -f "nc -l -p $PORT" >/dev/null 2>&1 || true
}
trap cleanup_transfer EXIT

echo "== 1. Crear namespace y par veth =="
ip netns add "$NS"
ip link add "$VETH_HOST" type veth peer name "$VETH_NS"
ip link set "$VETH_NS" netns "$NS"

ip addr add "$IP_HOST" dev "$VETH_HOST"
ip link set "$VETH_HOST" up

ip netns exec "$NS" ip addr add "$IP_NS" dev "$VETH_NS"
ip netns exec "$NS" ip link set "$VETH_NS" up
ip netns exec "$NS" ip link set lo up

echo
echo "== 2. Generar archivo de prueba de ${FILE_SIZE_MB}MB =="
dd if=/dev/urandom of="$FILE" bs=1M count="$FILE_SIZE_MB" status=none

transfer() {
    local label="$1"
    ip netns exec "$NS" sh -c "nc -l -p $PORT > /dev/null" &
    local listener_pid=$!
    sleep 1
    local start end elapsed mbps
    start=$(date +%s.%N)
    nc -N -w 30 "${IP_NS%/*}" "$PORT" < "$FILE"
    end=$(date +%s.%N)
    wait "$listener_pid" 2>/dev/null || true
    elapsed=$(echo "$end - $start" | bc)
    mbps=$(echo "scale=2; ($FILE_SIZE_MB * 8) / $elapsed" | bc)
    echo "${label}: ${elapsed}s -> ${mbps} mbit/s"
}

echo
echo "== 3. Transferencia SIN shaping (baseline) =="
transfer "baseline"

echo
echo "== 4. Aplicar tc htb: limitar egreso de ${VETH_HOST} a ${RATE} =="
tc qdisc add dev "$VETH_HOST" root handle 1: htb default 12
tc class add dev "$VETH_HOST" parent 1: classid 1:12 htb rate "$RATE"
tc -s qdisc show dev "$VETH_HOST"

echo
echo "== 5. Transferencia CON shaping (deberia acercarse a ${RATE}) =="
transfer "shaped"

echo
echo "Listo. Compara los mbit/s de 'baseline' vs 'shaped': el segundo debe"
echo "acercarse a ${RATE} mientras que el primero refleja el ancho de banda"
echo "real del par veth (sin limite artificial)."
echo "Corre ./cleanup.sh para eliminar namespace, veth y el qdisc."
