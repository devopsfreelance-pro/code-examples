#!/usr/bin/env python3
"""
Distribuye el costo mensual de un cluster compartido entre equipos,
en proporcion al uso real de CPU medido via Prometheus + cAdvisor.

Version mini del patron "SharedCostAllocator" del post:
https://www.devopsfreelance.pro/blog/posts/cost-allocation-showback-cloud/

Uso:
    python3 allocate_costs.py
    CLUSTER_MONTHLY_COST=5000 python3 allocate_costs.py
"""
import json
import os
import sys
from urllib.parse import urlencode
from urllib.request import urlopen

PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://localhost:9090")
CLUSTER_MONTHLY_COST = float(os.environ.get("CLUSTER_MONTHLY_COST", "3000"))
PROM_RANGE = os.environ.get("PROM_RANGE", "2m")
MAPPING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "team_mapping.json")


def query_prometheus(promql: str) -> list:
    params = urlencode({"query": promql})
    url = f"{PROMETHEUS_URL}/api/v1/query?{params}"
    with urlopen(url, timeout=10) as resp:
        payload = json.load(resp)
    if payload["status"] != "success":
        raise RuntimeError(f"Query Prometheus fallida: {payload}")
    return payload["data"]["result"]


def get_cpu_usage_by_container() -> dict:
    promql = (
        'sum by (name) (rate(container_cpu_usage_seconds_total'
        f'{{name=~"team-.*"}}[{PROM_RANGE}]))'
    )
    result = query_prometheus(promql)
    usage = {}
    for series in result:
        name = series["metric"].get("name")
        value = float(series["value"][1])
        if name:
            usage[name] = value
    return usage


def load_team_mapping() -> dict:
    with open(MAPPING_FILE) as f:
        return json.load(f)


def calculate_cost_distribution(usage: dict) -> dict:
    total = sum(usage.values())
    if total <= 0:
        raise RuntimeError(
            "No hay uso de CPU medido todavia. Espera 1-2 minutos tras "
            "'docker compose up' y volve a intentar."
        )
    return {
        name: {
            "cpu_share": value / total,
            "cost": round((value / total) * CLUSTER_MONTHLY_COST, 2),
        }
        for name, value in usage.items()
    }


def main():
    usage = get_cpu_usage_by_container()
    if not usage:
        print(
            "No se encontraron metricas 'container_cpu_usage_seconds_total' "
            "con name=~'team-.*'. Verifica que cAdvisor y Prometheus esten "
            "corriendo (docker compose ps) y que hayan pasado unos minutos.",
            file=sys.stderr,
        )
        sys.exit(1)

    distribution = calculate_cost_distribution(usage)
    mapping = load_team_mapping()

    print(f"Costo mensual del cluster compartido: ${CLUSTER_MONTHLY_COST:,.2f}\n")
    header = f"{'Team':<15}{'Cost Center':<15}{'CPU share':>12}{'Costo asignado':>18}"
    print(header)
    print("-" * len(header))
    for container, data in sorted(
        distribution.items(), key=lambda kv: kv[1]["cost"], reverse=True
    ):
        info = mapping.get(container, {"team": container, "cost_center": "N/A"})
        cost_str = "$" + format(data["cost"], ",.2f")
        print(
            f"{info['team']:<15}{info['cost_center']:<15}"
            f"{data['cpu_share'] * 100:>10.1f}%"
            f"{cost_str:>18}"
        )


if __name__ == "__main__":
    main()
