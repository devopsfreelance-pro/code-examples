#!/usr/bin/env python3
"""
Calculadora de error budget para el equipo owner de un servicio.

Lee los SLOs definidos en slo_config.yaml (la matriz de ownership del post
del blog define quien es responsable de cumplir estos numeros) y los datos
de trafico diarios en sample_metrics.csv, y calcula:

  - Consumo del error budget de disponibilidad y de latencia.
  - Burn rate (cuan rapido se esta gastando el budget vs. lo esperado
    para la ventana de 30 dias).
  - Una recomendacion operativa, tal como se describe en la seccion
    "Error budget como herramienta de decision" del post: budget sano
    -> se puede asumir mas riesgo; budget bajo -> priorizar estabilidad.

Uso:
    python3 error_budget_calculator.py
    python3 error_budget_calculator.py --slo slo_config.yaml --metrics sample_metrics.csv
"""

import argparse
import csv
import sys
from dataclasses import dataclass

import yaml


@dataclass
class DayMetrics:
    date: str
    total_requests: int
    failed_requests: int
    slow_requests: int


def load_slo_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if not config or "slos" not in config:
        raise ValueError(f"{path} no tiene una clave 'slos' valida")
    return config


def load_metrics(path: str) -> list:
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                DayMetrics(
                    date=row["date"],
                    total_requests=int(row["total_requests"]),
                    failed_requests=int(row["failed_requests"]),
                    slow_requests=int(row["slow_requests"]),
                )
            )
    if not rows:
        raise ValueError(f"{path} no tiene filas de metricas")
    return rows


def evaluate_slo(name: str, target_pct: float, good_events: int, total_events: int) -> dict:
    if total_events == 0:
        raise ValueError(f"total_events en 0 para el SLO '{name}'")

    achieved_pct = 100.0 * good_events / total_events
    allowed_bad_fraction = 1 - (target_pct / 100.0)
    allowed_bad_events = allowed_bad_fraction * total_events
    bad_events = total_events - good_events

    budget_consumed_pct = (
        100.0 * bad_events / allowed_bad_events if allowed_bad_events > 0 else float("inf")
    )

    return {
        "name": name,
        "target_pct": target_pct,
        "achieved_pct": achieved_pct,
        "bad_events": bad_events,
        "allowed_bad_events": allowed_bad_events,
        "budget_consumed_pct": budget_consumed_pct,
    }


def recommendation(budget_consumed_pct: float, days_elapsed: int, window_days: int) -> str:
    expected_consumed_pct = 100.0 * days_elapsed / window_days
    burn_rate = budget_consumed_pct / expected_consumed_pct if expected_consumed_pct > 0 else 0

    if budget_consumed_pct >= 100:
        return (
            f"BUDGET AGOTADO (burn rate {burn_rate:.1f}x). Congelar deployments no criticos, "
            "priorizar estabilidad y root-cause del incidente que lo consumio."
        )
    if budget_consumed_pct >= 80:
        return (
            f"BUDGET BAJO (burn rate {burn_rate:.1f}x). Reducir frecuencia de deployments, "
            "invertir en tests y resiliencia antes de tomar mas riesgo."
        )
    if burn_rate >= 2:
        return (
            f"BUDGET OK pero burn rate alto ({burn_rate:.1f}x lo esperado). Investigar la causa "
            "antes de que se convierta en un problema de fin de ventana."
        )
    return (
        f"BUDGET SANO (burn rate {burn_rate:.1f}x). El equipo puede asumir mas riesgo: "
        "deployments frecuentes, features experimentales."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slo", default="slo_config.yaml", help="Archivo de configuracion de SLOs")
    parser.add_argument("--metrics", default="sample_metrics.csv", help="CSV de metricas diarias")
    args = parser.parse_args()

    config = load_slo_config(args.slo)
    metrics = load_metrics(args.metrics)
    window_days = int(config.get("window_days", 30))

    total_requests = sum(m.total_requests for m in metrics)
    total_failed = sum(m.failed_requests for m in metrics)
    total_slow = sum(m.slow_requests for m in metrics)
    days_elapsed = len(metrics)

    print(f"Servicio: {config.get('service')}  |  Owner: {config.get('owner_team')}")
    print(f"Ventana: {window_days} dias  |  Dias con datos: {days_elapsed}")
    print(f"Requests totales en el periodo: {total_requests}\n")

    exit_code = 0

    for slo in config["slos"]:
        name = slo["name"]
        target_pct = float(slo["target_pct"])

        if name.lower() == "availability":
            good_events = total_requests - total_failed
        elif name.lower() == "latency":
            good_events = total_requests - total_slow
        else:
            print(f"[WARN] SLO desconocido '{name}', se omite (agregar logica en el script)")
            continue

        result = evaluate_slo(name, target_pct, good_events, total_requests)
        rec = recommendation(result["budget_consumed_pct"], days_elapsed, window_days)

        print(f"--- SLO: {result['name']} ---")
        print(f"  Target:            {result['target_pct']:.3f}%")
        print(f"  Alcanzado:         {result['achieved_pct']:.4f}%")
        print(f"  Eventos malos:     {result['bad_events']} (permitidos: {result['allowed_bad_events']:.1f})")
        print(f"  Budget consumido:  {result['budget_consumed_pct']:.1f}%")
        print(f"  Recomendacion:     {rec}\n")

        if result["budget_consumed_pct"] >= 100:
            exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
