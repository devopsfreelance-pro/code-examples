#!/usr/bin/env bash
# Elimina todos los recursos creados por policy-routing-lab.sh y
# tc-bandwidth-shaping.sh. Idempotente: se puede correr aunque los
# recursos ya no existan.
set +e

echo "== Limpiando policy-routing-lab.sh =="
ip rule del from 10.10.1.0/24 table 100 priority 100 2>/dev/null
ip rule del from 10.10.2.0/24 table 200 priority 200 2>/dev/null
ip route flush table 100 2>/dev/null
ip route flush table 200 2>/dev/null
ip link del dummy1 2>/dev/null
ip link del dummy2 2>/dev/null

echo "== Limpiando tc-bandwidth-shaping.sh =="
ip netns exec shaped-ns pkill -f "nc -l -p 5001" 2>/dev/null
tc qdisc del dev veth-host root 2>/dev/null
ip link del veth-host 2>/dev/null
ip netns del shaped-ns 2>/dev/null
rm -f /tmp/tc-test-payload.bin

echo
echo "Limpieza completa."
