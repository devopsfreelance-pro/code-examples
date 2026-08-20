#!/usr/bin/env bash
# Demuestra dos ideas del post:
#  a) el orden de las reglas en iptables importa (evalua de arriba a abajo,
#     aplica la primera coincidencia)
#  b) el equivalente nftables de la misma politica (SSH permitido, resto DROP)
set -euo pipefail

echo "############################################"
echo "# A) iptables: orden de las reglas importa #"
echo "############################################"

echo
echo "-- Politica CORRECTA: primero ACCEPT de SSH, despues DROP general --"
iptables -F INPUT || true
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -j DROP
echo "Reglas cargadas:"
iptables -L INPUT -n --line-numbers

echo
echo "-- Comprobacion: el trafico SSH (puerto 22) matchea la regla 1 (ACCEPT) --"
iptables -C INPUT -p tcp --dport 22 -j ACCEPT && echo "OK: la regla ACCEPT de SSH esta activa"

echo
echo "-- Politica INCORRECTA (la que menciona el post): DROP antes del ACCEPT --"
echo "   Si esto se aplicara en una sesion SSH remota real, el DROP se evalua"
echo "   primero y la conexion se corta antes de llegar a la regla ACCEPT."
iptables -F INPUT
iptables -A INPUT -j DROP
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
echo "Reglas cargadas (ORDEN INCORRECTO, solo a modo ilustrativo):"
iptables -L INPUT -n --line-numbers
iptables -F INPUT

echo
echo "########################################################"
echo "# B) nftables: la misma politica con el frontend nuevo #"
echo "########################################################"
echo
nft add table inet filter
nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'
nft add rule inet filter input ct state established,related accept
nft add rule inet filter input tcp dport 22 accept
echo "Tabla nftables creada (se omiten otras tablas del sistema, p.ej. las de Docker):"
nft list table inet filter
nft delete table inet filter

echo
echo "Listo. Ambos bloques quedaron limpios (INPUT de iptables vaciada, tabla nftables eliminada)."
