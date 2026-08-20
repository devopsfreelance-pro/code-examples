#!/usr/bin/env python3
"""
diversity_calculator.py

Calcula el riesgo de concentracion de clientes en una red Ethereum
a partir de una distribucion de mercado (execution layer y consensus
layer), aplicando los umbrales de riesgo que usa la comunidad:

  - >33% de un solo cliente: riesgo de finalidad afectada si falla.
  - >50% de un solo cliente: riesgo de que una cadena invalida gane
    la mayoria simple.
  - >66% de un solo cliente: riesgo de finalizacion incorrecta /
    slashing masivo (umbral de supermayoria de Casper FFG).

Tambien calcula el indice Herfindahl-Hirschman (HHI) normalizado
(0 a 1) como medida agregada de concentracion: valores cercanos a 0
indican alta diversidad, valores cercanos a 1 indican monopolio de
un cliente.

Uso:
    python3 diversity_calculator.py sample_distribution.json
"""

from __future__ import annotations

import json
import sys
from typing import Dict


THRESHOLDS = (
    (66.0, "CRITICO"),
    (50.0, "ALTO"),
    (33.0, "MEDIO"),
)


def herfindahl_index(shares: Dict[str, float]) -> float:
    """HHI normalizado en escala 0-1 a partir de porcentajes (0-100)."""
    total = sum(shares.values())
    if total == 0:
        return 0.0
    fractions = [v / total for v in shares.values()]
    return sum(f * f for f in fractions)


def risk_level(max_share: float) -> str:
    for threshold, label in THRESHOLDS:
        if max_share >= threshold:
            return label
    return "BAJO"


def evaluate_layer(name: str, shares: Dict[str, float]) -> None:
    total = sum(shares.values())
    if abs(total - 100.0) > 1.0:
        print(f"  [!] Advertencia: los porcentajes suman {total:.1f}%, no 100%")

    dominant_client, dominant_share = max(shares.items(), key=lambda kv: kv[1])
    hhi = herfindahl_index(shares)
    level = risk_level(dominant_share)

    print(f"\n== {name} ==")
    for client, share in sorted(shares.items(), key=lambda kv: -kv[1]):
        bar = "#" * int(share / 2)
        print(f"  {client:<12} {share:5.1f}%  {bar}")

    print(f"  Cliente dominante : {dominant_client} ({dominant_share:.1f}%)")
    print(f"  Indice HHI        : {hhi:.3f} (0=diverso, 1=monopolio)")
    print(f"  Nivel de riesgo   : {level}")

    if level in ("CRITICO", "ALTO"):
        minority = sorted(shares.items(), key=lambda kv: kv[1])[:2]
        sugeridos = ", ".join(c for c, _ in minority)
        print(f"  Sugerencia        : migrar nodos hacia {sugeridos} para reducir riesgo")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Uso: {sys.argv[0]} <archivo_distribucion.json>", file=sys.stderr)
        return 1

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    print(f"Analisis de client diversity: {data.get('description', path)}")

    exit_code = 0
    for layer_key, layer_label in (
        ("execution_layer", "Execution Layer"),
        ("consensus_layer", "Consensus Layer"),
    ):
        shares = data.get(layer_key)
        if not shares:
            continue
        evaluate_layer(layer_label, shares)
        dominant_share = max(shares.values())
        if risk_level(dominant_share) in ("CRITICO", "ALTO"):
            exit_code = 2

    print()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
