#!/usr/bin/env python3
"""
analyze_costs.py - Mini motor FinOps: Fase "Informar" + Fase "Optimizar"

Simula lo que haría un script contra el AWS Cost & Usage Report (CUR) o la
API de Cost Explorer, pero trabajando sobre un CSV local para que se pueda
correr sin credenciales de AWS. Aplica tres reglas típicas de un Centro de
Excelencia FinOps:

1. Visibilidad (Informar): detecta recursos sin tags de 'environment' o
   'cost_center' (bloquean el chargeback/showback correcto).
2. Right-sizing (Optimizar): marca instancias con utilización de CPU baja
   (< UTILIZATION_THRESHOLD) como candidatas a downsizing o apagado.
3. Recursos huérfanos: volúmenes EBS sin ninguna tag, típicos de instancias
   ya borradas, que se recomiendan eliminar directamente.

Uso:
    python3 analyze_costs.py sample_cost_data.csv
    python3 analyze_costs.py sample_cost_data.csv --utilization-threshold 15
"""
import argparse
import csv
import sys
from collections import defaultdict

UTILIZATION_THRESHOLD_DEFAULT = 15.0
RIGHT_SIZING_SAVINGS_ESTIMATE = 0.5  # 50% de ahorro estimado al hacer right-sizing


def parse_row(row):
    row = dict(row)
    row["daily_cost_usd"] = float(row["daily_cost_usd"]) if row["daily_cost_usd"] else 0.0
    cpu = row.get("avg_cpu_utilization_pct", "")
    row["avg_cpu_utilization_pct"] = float(cpu) if cpu not in ("", None) else None
    return row


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [parse_row(r) for r in reader]


def find_untagged(rows):
    return [
        r for r in rows
        if not r.get("environment") or not r.get("cost_center")
    ]


def find_orphan_ebs(rows):
    return [
        r for r in rows
        if r["service"] == "EBS" and not r.get("environment") and not r.get("cost_center")
    ]


def find_rightsizing_candidates(rows, threshold):
    candidates = []
    for r in rows:
        cpu = r["avg_cpu_utilization_pct"]
        if cpu is not None and cpu < threshold and r["daily_cost_usd"] > 0:
            candidates.append(r)
    return candidates


def group_cost_by(rows, key):
    totals = defaultdict(float)
    for r in rows:
        value = r.get(key) or "(sin etiqueta)"
        totals[value] += r["daily_cost_usd"]
    return dict(sorted(totals.items(), key=lambda kv: kv[1], reverse=True))


def print_section(title):
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(description="Mini motor de análisis FinOps sobre un CSV de costos")
    parser.add_argument("csv_path", help="Ruta al CSV con datos de costo (ver sample_cost_data.csv)")
    parser.add_argument(
        "--utilization-threshold",
        type=float,
        default=UTILIZATION_THRESHOLD_DEFAULT,
        help=f"Umbral de CPU %% bajo el cual un recurso es candidato a right-sizing (default: {UTILIZATION_THRESHOLD_DEFAULT})",
    )
    args = parser.parse_args()

    rows = load_rows(args.csv_path)
    total_daily_cost = sum(r["daily_cost_usd"] for r in rows)

    print_section("FASE 1: INFORMAR - Visibilidad y asignación de costos")
    print(f"Gasto diario total analizado: USD {total_daily_cost:,.2f}")
    print(f"Gasto mensual proyectado (x30): USD {total_daily_cost * 30:,.2f}")

    by_env = group_cost_by(rows, "environment")
    print("\nCosto diario por ambiente:")
    for env, cost in by_env.items():
        print(f"  {env:20s} USD {cost:8.2f}")

    by_cc = group_cost_by(rows, "cost_center")
    print("\nCosto diario por cost center:")
    for cc, cost in by_cc.items():
        print(f"  {cc:20s} USD {cost:8.2f}")

    untagged = find_untagged(rows)
    untagged_cost = sum(r["daily_cost_usd"] for r in untagged)
    coverage_pct = 100 * (1 - len(untagged) / len(rows)) if rows else 0
    print(f"\nCobertura de etiquetado: {coverage_pct:.1f}% ({len(rows) - len(untagged)}/{len(rows)} recursos)")
    print(f"Gasto diario sin trazabilidad completa (falta environment o cost_center): USD {untagged_cost:,.2f}")
    if untagged:
        print("Recursos sin etiquetar correctamente:")
        for r in untagged:
            print(f"  - {r['resource_id']:28s} ({r['service']}) USD {r['daily_cost_usd']:.2f}/día")

    print_section("FASE 2: OPTIMIZAR - Right-sizing y recursos huérfanos")
    orphans = find_orphan_ebs(rows)
    orphan_cost = sum(r["daily_cost_usd"] for r in orphans)
    if orphans:
        print(f"Volúmenes EBS huérfanos detectados: {len(orphans)} (USD {orphan_cost:,.2f}/día = USD {orphan_cost*30:,.2f}/mes)")
        for r in orphans:
            print(f"  - {r['resource_id']:28s} USD {r['daily_cost_usd']:.2f}/día -> recomendación: eliminar")
    else:
        print("Sin volúmenes EBS huérfanos.")

    candidates = find_rightsizing_candidates(rows, args.utilization_threshold)
    candidates_cost = sum(r["daily_cost_usd"] for r in candidates)
    estimated_savings = candidates_cost * RIGHT_SIZING_SAVINGS_ESTIMATE
    print(f"\nCandidatos a right-sizing (CPU < {args.utilization_threshold:.0f}%): {len(candidates)}")
    for r in candidates:
        print(
            f"  - {r['resource_id']:28s} ({r['instance_type'] or r['service']}) "
            f"CPU {r['avg_cpu_utilization_pct']:.0f}% USD {r['daily_cost_usd']:.2f}/día"
        )
    print(f"\nAhorro mensual estimado por right-sizing (50% de reducción típica): USD {estimated_savings * 30:,.2f}")

    print_section("RESUMEN EJECUTIVO")
    total_opportunity = (orphan_cost + estimated_savings) * 30
    print(f"Oportunidad de ahorro mensual identificada: USD {total_opportunity:,.2f}")
    print(f"  - Eliminación de huérfanos:  USD {orphan_cost * 30:,.2f}/mes")
    print(f"  - Right-sizing:              USD {estimated_savings * 30:,.2f}/mes")
    print(f"Esto representa el {100 * total_opportunity / (total_daily_cost * 30):.1f}% del gasto mensual proyectado.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
