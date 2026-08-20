#!/usr/bin/env bash
# Demuestra "Tablas de Enrutamiento Multiples" y "Policy-Based Routing" del
# post: dos interfaces con direcciones de origen distintas, cada una atada a
# su propia tabla de rutas mediante `ip rule`, y verificacion con
# `ip route get` de que el kernel elige la tabla correcta segun el origen.
set -euo pipefail

DUMMY_A=dummy1
DUMMY_B=dummy2
NET_A=10.10.1.0/24
NET_B=10.10.2.0/24
IP_A=10.10.1.1/24
IP_B=10.10.2.1/24
TABLE_A=100
TABLE_B=200
DEST=8.8.8.8

echo "== 1. Crear dos interfaces dummy (simulan dos uplinks / ISPs) =="
ip link add "$DUMMY_A" type dummy
ip link add "$DUMMY_B" type dummy
ip addr add "$IP_A" dev "$DUMMY_A"
ip addr add "$IP_B" dev "$DUMMY_B"
ip link set "$DUMMY_A" up
ip link set "$DUMMY_B" up

echo
echo "== 2. Crear una tabla de rutas por cada uplink =="
ip route add default dev "$DUMMY_A" table "$TABLE_A"
ip route add default dev "$DUMMY_B" table "$TABLE_B"

echo
echo "== 3. Reglas de politica: el trafico con origen en cada red usa su tabla =="
ip rule add from "$NET_A" table "$TABLE_A" priority 100
ip rule add from "$NET_B" table "$TABLE_B" priority 200

echo
echo "== 4. Reglas activas (ip rule show) =="
ip rule show

echo
echo "== 5. Verificar que el kernel elige la tabla/interfaz correcta segun el origen =="
echo "--- paquete con origen en ${NET_A} hacia ${DEST} ---"
ip route get "$DEST" from "${IP_A%/*}"
echo
echo "--- paquete con origen en ${NET_B} hacia ${DEST} ---"
ip route get "$DEST" from "${IP_B%/*}"

echo
echo "== 6. Resumen de tablas =="
echo "--- tabla ${TABLE_A} (uplink A) ---"
ip route show table "$TABLE_A"
echo "--- tabla ${TABLE_B} (uplink B) ---"
ip route show table "$TABLE_B"

echo
echo "Listo. La salida de 'ip route get' del paso 5 debe mostrar 'dev dummy1'"
echo "para el origen de la red A y 'dev dummy2' para el origen de la red B,"
echo "confirmando que el policy-based routing selecciono la tabla correcta."
echo "Corre ./cleanup.sh para eliminar interfaces, tablas y reglas."
