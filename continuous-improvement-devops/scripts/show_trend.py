#!/usr/bin/env python3
"""Lee metrics_history.json y muestra la evolucion de las metricas
entre iteraciones, con veredicto de mejora/empeoro por metrica.

Es el paso "Check" del ciclo PDCA que describe el post: convierte la
historia de metricas del pipeline en una decision (consolidar la
mejora o revisar el siguiente experimento).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HISTORY_FILE = ROOT / "metrics_history.json"

# Para cada metrica, True si "menos es mejor"
LOWER_IS_BETTER = {
    "pylint_issues": True,
    "complexity_avg": True,
    "coverage_pct": False,
}


def verdict(metric: str, previous: float, current: float) -> str:
    if current == previous:
        return "sin cambio"
    improved = (current < previous) if LOWER_IS_BETTER[metric] else (current > previous)
    return "mejora" if improved else "empeora"


def main() -> None:
    if not HISTORY_FILE.exists():
        print("No hay metrics_history.json. Corre collect_metrics.py primero.")
        sys.exit(1)

    history = json.loads(HISTORY_FILE.read_text())
    if not history:
        print("metrics_history.json esta vacio.")
        sys.exit(1)

    print(f"{'iteracion':<10} {'pylint_issues':<15} {'complexity_avg':<16} {'coverage_pct':<14}")
    for entry in history:
        print(
            f"{entry['label']:<10} {entry['pylint_issues']:<15} "
            f"{entry['complexity_avg']:<16} {entry['coverage_pct']:<14}"
        )

    if len(history) < 2:
        print("\nSe necesita mas de una iteracion para calcular tendencia.")
        return

    print("\n=== Tendencia entre iteraciones (ciclo PDCA: paso Check) ===")
    for prev, curr in zip(history, history[1:]):
        print(f"\n{prev['label']} -> {curr['label']}:")
        for metric in ("pylint_issues", "complexity_avg", "coverage_pct"):
            v = verdict(metric, prev[metric], curr[metric])
            print(f"  {metric}: {prev[metric]} -> {curr[metric]}  ({v})")


if __name__ == "__main__":
    main()
