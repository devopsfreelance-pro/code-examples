#!/usr/bin/env python3
"""
rightsizing_analyzer.py

Aplica las reglas explicitas de rightsizing descriptas en el post
"Rightsizing de Recursos Cloud" a una serie de metricas de utilizacion
(CPU y memoria) y devuelve una recomendacion por recurso.

Reglas (ver post, seccion "Decidir con reglas explicitas"):
  - p99 CPU < 40% y p99 memoria < 50% durante la ventana -> bajar un tamano
  - utilizacion nula/testimonial (CPU < 3%) -> candidato a apagado
  - resto -> mantener tamano actual

No requiere dependencias externas: usa solo la libreria estandar de Python.
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
from dataclasses import dataclass, field


CPU_DOWNSIZE_THRESHOLD = 40.0
MEM_DOWNSIZE_THRESHOLD = 50.0
IDLE_CPU_THRESHOLD = 3.0


@dataclass
class ResourceSamples:
    resource_id: str
    cpu_samples: list[float] = field(default_factory=list)
    mem_samples: list[float] = field(default_factory=list)


def percentile(values: list[float], pct: float) -> float:
    """Percentil simple por interpolacion lineal (sin dependencias externas)."""
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    k = (len(ordered) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(ordered) - 1)
    if f == c:
        return ordered[f]
    return ordered[f] + (ordered[c] - ordered[f]) * (k - f)


def load_samples(csv_path: str) -> dict[str, ResourceSamples]:
    """
    Espera un CSV con columnas: resource_id,cpu_pct,mem_pct
    Una fila por muestra (ej: una lectura horaria durante 14 dias).
    """
    resources: dict[str, ResourceSamples] = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"resource_id", "cpu_pct", "mem_pct"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise ValueError(
                f"El CSV debe tener columnas {sorted(required)}, "
                f"encontradas: {reader.fieldnames}"
            )
        for row in reader:
            rid = row["resource_id"].strip()
            if rid not in resources:
                resources[rid] = ResourceSamples(resource_id=rid)
            resources[rid].cpu_samples.append(float(row["cpu_pct"]))
            resources[rid].mem_samples.append(float(row["mem_pct"]))
    return resources


def classify(samples: ResourceSamples) -> dict:
    cpu_p99 = percentile(samples.cpu_samples, 99)
    mem_p99 = percentile(samples.mem_samples, 99)
    cpu_avg = statistics.mean(samples.cpu_samples)
    mem_avg = statistics.mean(samples.mem_samples)

    if cpu_p99 < IDLE_CPU_THRESHOLD:
        verdict = "APAGAR (ocioso)"
    elif cpu_p99 < CPU_DOWNSIZE_THRESHOLD and mem_p99 < MEM_DOWNSIZE_THRESHOLD:
        verdict = "BAJAR UN TAMANO (rightsizing)"
    else:
        verdict = "MANTENER (uso justifica el tamano actual)"

    return {
        "resource_id": samples.resource_id,
        "cpu_avg": round(cpu_avg, 1),
        "cpu_p99": round(cpu_p99, 1),
        "mem_avg": round(mem_avg, 1),
        "mem_p99": round(mem_p99, 1),
        "samples": len(samples.cpu_samples),
        "verdict": verdict,
    }


def print_report(results: list[dict]) -> None:
    header = f"{'recurso':<20}{'cpu_avg':>9}{'cpu_p99':>9}{'mem_avg':>9}{'mem_p99':>9}{'muestras':>10}   veredicto"
    print(header)
    print("-" * len(header))
    for r in results:
        print(
            f"{r['resource_id']:<20}{r['cpu_avg']:>8}%{r['cpu_p99']:>8}%"
            f"{r['mem_avg']:>8}%{r['mem_p99']:>8}%{r['samples']:>10}   {r['verdict']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Clasifica recursos cloud segun reglas de rightsizing por percentil."
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        default="sample_metrics.csv",
        help="CSV con columnas resource_id,cpu_pct,mem_pct (default: sample_metrics.csv)",
    )
    args = parser.parse_args()

    try:
        resources = load_samples(args.csv_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not resources:
        print("El CSV no contiene filas.", file=sys.stderr)
        return 1

    results = [classify(s) for s in resources.values()]
    results.sort(key=lambda r: r["resource_id"])
    print_report(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
