#!/usr/bin/env python3
"""
dora_metrics.py

Calcula las 4 metricas DORA (deployment frequency, lead time for changes,
time to restore service, change failure rate) para dos sprints consecutivos
y muestra la variacion entre ambos, tal como las revisaria un equipo en una
retrospectiva kaizen devops: "¿mejoramos respecto al sprint anterior?".

Los datos son sinteticos (deployments_sample.json) y representan un equipo
que, tras una retrospectiva, decide desplegar en lotes mas chicos y mas
frecuentes. El script cuantifica el efecto de esa decision en las 4
metricas DORA, que es exactamente el ciclo "hipotesis -> cambio -> medicion"
descripto en la seccion "Process optimization mediante metricas DORA" del
post.

Uso:
    python3 dora_metrics.py deployments_sample.json

No requiere dependencias externas (solo libreria estandar).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from statistics import median


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def deployment_frequency(deployments: list[dict], period_days: int) -> float:
    """Despliegues por dia en el periodo evaluado."""
    if period_days <= 0:
        return 0.0
    return len(deployments) / period_days


def lead_time_hours(deployments: list[dict]) -> float:
    """Mediana de horas entre el commit y el despliegue a produccion."""
    deltas = []
    for d in deployments:
        commit_at = parse_dt(d["commit_at"])
        deployed_at = parse_dt(d["deployed_at"])
        deltas.append((deployed_at - commit_at).total_seconds() / 3600)
    return median(deltas) if deltas else 0.0


def time_to_restore_hours(incidents: list[dict]) -> float:
    """Mediana de horas entre el inicio y la resolucion de un incidente."""
    deltas = []
    for inc in incidents:
        started_at = parse_dt(inc["started_at"])
        resolved_at = parse_dt(inc["resolved_at"])
        deltas.append((resolved_at - started_at).total_seconds() / 3600)
    return median(deltas) if deltas else 0.0


def change_failure_rate(deployments: list[dict], incidents: list[dict]) -> float:
    """Porcentaje de despliegues que provocaron al menos un incidente."""
    if not deployments:
        return 0.0
    deployment_ids_with_incident = {inc["caused_by_deployment"] for inc in incidents}
    failed = sum(1 for d in deployments if d["id"] in deployment_ids_with_incident)
    return (failed / len(deployments)) * 100


def classify_deployment_frequency(per_day: float) -> str:
    if per_day >= 1:
        return "Elite (varios por dia / diario)"
    if per_day >= 1 / 7:
        return "High (semanal a mensual)"
    if per_day >= 1 / 30:
        return "Medium (mensual a semestral)"
    return "Low (menos de una vez por semestre)"


def classify_lead_time(hours: float) -> str:
    if hours < 24:
        return "Elite (menos de un dia)"
    if hours < 24 * 7:
        return "High (un dia a una semana)"
    if hours < 24 * 30 * 6:
        return "Medium (una semana a seis meses)"
    return "Low (mas de seis meses)"


def classify_ttr(hours: float) -> str:
    if hours < 1:
        return "Elite (menos de una hora)"
    if hours < 24:
        return "High (menos de un dia)"
    if hours < 24 * 7:
        return "Medium (menos de una semana)"
    return "Low (mas de una semana)"


def classify_cfr(percent: float) -> str:
    if percent <= 15:
        return "Elite/High (0-15%)"
    if percent <= 30:
        return "Medium (16-30%)"
    return "Low (mas de 30%)"


def compute_sprint_metrics(sprint: dict) -> dict:
    deployments = sprint["deployments"]
    incidents = sprint["incidents"]
    period_days = sprint["period_days"]

    df = deployment_frequency(deployments, period_days)
    lt = lead_time_hours(deployments)
    ttr = time_to_restore_hours(incidents)
    cfr = change_failure_rate(deployments, incidents)

    return {
        "label": sprint["label"],
        "deployment_frequency_per_day": df,
        "deployment_frequency_level": classify_deployment_frequency(df),
        "lead_time_hours": lt,
        "lead_time_level": classify_lead_time(lt),
        "time_to_restore_hours": ttr,
        "time_to_restore_level": classify_ttr(ttr),
        "change_failure_rate_pct": cfr,
        "change_failure_rate_level": classify_cfr(cfr),
    }


def print_report(metrics: dict) -> None:
    print(f"\n=== {metrics['label']} ===")
    print(
        f"  Deployment frequency : {metrics['deployment_frequency_per_day']:.2f} despliegues/dia"
        f"  -> {metrics['deployment_frequency_level']}"
    )
    print(
        f"  Lead time for changes: {metrics['lead_time_hours']:.1f} horas"
        f"  -> {metrics['lead_time_level']}"
    )
    print(
        f"  Time to restore      : {metrics['time_to_restore_hours']:.2f} horas"
        f"  -> {metrics['time_to_restore_level']}"
    )
    print(
        f"  Change failure rate  : {metrics['change_failure_rate_pct']:.1f}%"
        f"  -> {metrics['change_failure_rate_level']}"
    )


def print_delta(before: dict, after: dict) -> None:
    print("\n=== Variacion sprint 1 -> sprint 2 (efecto de las mejoras kaizen) ===")

    df_delta = after["deployment_frequency_per_day"] - before["deployment_frequency_per_day"]
    lt_delta = after["lead_time_hours"] - before["lead_time_hours"]
    ttr_delta = after["time_to_restore_hours"] - before["time_to_restore_hours"]
    cfr_delta = after["change_failure_rate_pct"] - before["change_failure_rate_pct"]

    print(f"  Deployment frequency : {df_delta:+.2f} despliegues/dia")
    print(f"  Lead time for changes: {lt_delta:+.1f} horas")
    print(f"  Time to restore      : {ttr_delta:+.2f} horas")
    print(f"  Change failure rate  : {cfr_delta:+.1f} puntos porcentuales")

    mejoras = 0
    if df_delta > 0:
        mejoras += 1
    if lt_delta < 0:
        mejoras += 1
    if ttr_delta < 0:
        mejoras += 1
    if cfr_delta < 0:
        mejoras += 1

    print(f"\n  {mejoras}/4 metricas DORA mejoraron respecto al sprint anterior.")
    if mejoras >= 3:
        print("  Veredicto kaizen: las acciones definidas en la retrospectiva")
        print("  tuvieron impacto medible. Se consolidan y se busca la siguiente mejora.")
    else:
        print("  Veredicto kaizen: impacto insuficiente. Revisar en la proxima")
        print("  retrospectiva si las acciones eran las correctas.")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Uso: python3 {sys.argv[0]} <archivo.json>", file=sys.stderr)
        return 1

    path = sys.argv[1]
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error leyendo {path}: {exc}", file=sys.stderr)
        return 1

    metrics_sprint1 = compute_sprint_metrics(data["sprint_1"])
    metrics_sprint2 = compute_sprint_metrics(data["sprint_2"])

    print_report(metrics_sprint1)
    print_report(metrics_sprint2)
    print_delta(metrics_sprint1, metrics_sprint2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
