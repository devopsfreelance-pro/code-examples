#!/usr/bin/env python3
"""
Calcula el SLI de disponibilidad y de latencia consultando Prometheus,
los compara contra el SLO definido en el post y sugiere un SLA externo
mas conservador (tal como recomienda el post: "el SLA debe ser mas
conservador que el SLO interno").

Requiere que Prometheus este scrapeando el servicio demo (ver README) y
que haya trafico reciente en la ventana evaluada (correr load_test.sh
antes de este script).

Solo usa la libreria estandar de Python (urllib), sin dependencias extra.
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request

PROM_URL_DEFAULT = "http://localhost:9090"


def prom_query(prom_url, promql):
    url = f"{prom_url}/api/v1/query?{urllib.parse.urlencode({'query': promql})}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.load(resp)
    if data["status"] != "success":
        raise RuntimeError(f"Prometheus query fallo: {data}")
    return data["data"]["result"]


def scalar(result, default=0.0):
    if not result:
        return default
    return float(result[0]["value"][1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prometheus-url", default=PROM_URL_DEFAULT)
    parser.add_argument("--window", default="5m", help="Ventana de evaluacion (ej: 5m, 30m, 1h)")
    parser.add_argument("--slo-availability", type=float, default=0.999, help="fraccion, ej 0.999 = 99.9%")
    parser.add_argument("--slo-latency-p95", type=float, default=0.2, help="segundos")
    parser.add_argument("--sla-margin", type=float, default=0.004, help="colchon SLA vs SLO, en fraccion")
    args = parser.parse_args()

    w = args.window

    total = scalar(prom_query(
        args.prometheus_url,
        f'sum(increase(http_requests_total{{endpoint="/work"}}[{w}]))',
    ))
    errors_5xx = scalar(prom_query(
        args.prometheus_url,
        f'sum(increase(http_requests_total{{endpoint="/work",status=~"5.."}}[{w}]))',
    ))
    p95 = scalar(prom_query(
        args.prometheus_url,
        f'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{{endpoint="/work"}}[{w}])) by (le))',
    ), default=float("nan"))

    if total == 0:
        print("No hay trafico en la ventana evaluada. Corre ./load_test.sh primero.")
        sys.exit(2)

    availability_sli = 1 - (errors_5xx / total)
    sla_target = args.slo_availability - args.sla_margin

    print("=" * 60)
    print("REPORTE SLI / SLO / SLA")
    print("=" * 60)
    print(f"Ventana evaluada:            {w}")
    print(f"Solicitudes totales:         {total:.0f}")
    print(f"Errores 5xx:                 {errors_5xx:.0f}")
    print(f"SLI disponibilidad:          {availability_sli * 100:.3f}%")
    print(f"SLI latencia p95:            {p95 * 1000:.0f} ms")
    print("-" * 60)
    print(f"SLO disponibilidad objetivo: {args.slo_availability * 100:.3f}%")
    print(f"SLO latencia p95 objetivo:   {args.slo_latency_p95 * 1000:.0f} ms")

    avail_ok = availability_sli >= args.slo_availability
    latency_ok = (p95 == p95) and p95 <= args.slo_latency_p95  # p95 == p95 descarta NaN

    print(f"Cumple SLO disponibilidad:   {'SI' if avail_ok else 'NO'}")
    print(f"Cumple SLO latencia:         {'SI' if latency_ok else 'NO'}")
    print("-" * 60)
    print(f"SLA externo sugerido:        {sla_target * 100:.3f}% (colchon de {args.sla_margin * 100:.2f}pp bajo el SLO)")
    print("=" * 60)

    sys.exit(0 if (avail_ok and latency_ok) else 1)


if __name__ == "__main__":
    main()
