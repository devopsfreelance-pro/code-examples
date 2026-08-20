#!/usr/bin/env bash
# Demo: 4 escenarios contra la misma llave usando sample_interchange.json
# como estado previo (lo que un nodo real exportaria con
# `lighthouse account validator slashing-protection export`).
#
# Uso: ./demo.sh

set -uo pipefail

DB="sample_interchange.json"
PUBKEY="0xa1d1ad0714035353258038e964ae9675dc0252ee22cea896825c01458e1807bfad2f9969338798548d9858a571f7f5"

echo "== Escenario 1: attestation legitima (target epoch mayor a la ultima firmada) =="
python3 slashing_protection.py "$DB" check-attestation \
  --pubkey "$PUBKEY" \
  --source-epoch 3006 \
  --target-epoch 3008 \
  --signing-root "0xnuevoroot001"
echo

echo "== Escenario 2: DOBLE VOTO -- mismo target epoch ya firmado, root distinto =="
echo "   (simula un nodo de respaldo con las mismas llaves firmando en paralelo)"
python3 slashing_protection.py "$DB" check-attestation \
  --pubkey "$PUBKEY" \
  --source-epoch 2290 \
  --target-epoch 3007 \
  --signing-root "0xrootDIFERENTE-nodo-backup"
echo

echo "== Escenario 3: VOTO ENVOLVENTE -- intenta envolver la attestation ya firmada =="
python3 slashing_protection.py "$DB" check-attestation \
  --pubkey "$PUBKEY" \
  --source-epoch 2000 \
  --target-epoch 4000 \
  --signing-root "0xrootenvolvente"
echo

echo "== Escenario 4: DOBLE PROPUESTA DE BLOQUE -- mismo slot ya firmado, root distinto =="
python3 slashing_protection.py "$DB" check-block \
  --pubkey "$PUBKEY" \
  --slot 81952 \
  --signing-root "0xrootDIFERENTE-nodo-backup-block"
echo

echo "Escenarios 1 permitido; 2, 3 y 4 bloqueados. Ver README para el detalle."
