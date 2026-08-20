#!/usr/bin/env bash
# Demuestra el failover automatico del cluster activo-activo:
# 1) Hace varias requests y muestra que responden ambos nodos (roundrobin).
# 2) Apaga web1 (simula la caida de un nodo).
# 3) Muestra que HAProxy detecta el fallo (healthcheck) y todo el trafico
#    sigue siendo servido por web2, sin caidas de servicio.
# 4) Levanta web1 de nuevo y lo reincorpora al cluster.
set -uo pipefail

URL="http://localhost:8080"

echo "== 1) Trafico normal (activo-activo, round robin) =="
for i in $(seq 1 4); do
    curl -s "$URL" | grep -o "NODO [0-9]" || echo "(sin respuesta)"
    sleep 0.3
done

echo
echo "== 2) Simulando caida del nodo web1 =="
docker compose stop web1
echo "Esperando a que HAProxy marque web1 como down (health check)..."
sleep 5

echo
echo "== 3) Trafico durante el fallo (debe responder solo web2) =="
for i in $(seq 1 4); do
    curl -s "$URL" | grep -o "NODO [0-9]" || echo "(sin respuesta)"
    sleep 0.3
done

echo
echo "== 4) Recuperando el nodo web1 (failback) =="
docker compose start web1
sleep 5

echo
echo "== 5) Trafico tras la recuperacion (vuelve el balanceo entre ambos) =="
for i in $(seq 1 4); do
    curl -s "$URL" | grep -o "NODO [0-9]" || echo "(sin respuesta)"
    sleep 0.3
done

echo
echo "Prueba de failover completada."
