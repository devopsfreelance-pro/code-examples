"""
Prueba de confiabilidad basica: golpea /health durante N segundos y valida
los resultados contra un SLO de disponibilidad y de latencia, igual que el
patron "validate_deployment_reliability" descrito en el post (sin Datadog,
para poder correrlo local sin cuentas de terceros).

Uso:
    python reliability_test.py --duration 20 --interval 0.5 \
        --slo-success-rate 0.95 --slo-latency 0.3
"""
import argparse
import sys
import time

import requests

SERVICE_URL = "http://localhost:5000"


def run_reliability_test(duration_seconds, interval_seconds):
    metrics = {"total": 0, "success": 0, "latencies": []}

    end_time = time.time() + duration_seconds
    while time.time() < end_time:
        metrics["total"] += 1
        try:
            response = requests.get(f"{SERVICE_URL}/health", timeout=5)
            metrics["latencies"].append(response.elapsed.total_seconds())
            if response.status_code == 200:
                metrics["success"] += 1
        except requests.exceptions.RequestException:
            metrics["latencies"].append(5.0)

        time.sleep(interval_seconds)

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Reliability test contra un SLO")
    parser.add_argument("--duration", type=int, default=20, help="Duracion en segundos")
    parser.add_argument("--interval", type=float, default=0.5, help="Segundos entre peticiones")
    parser.add_argument("--slo-success-rate", type=float, default=0.95)
    parser.add_argument("--slo-latency", type=float, default=0.3, help="Latencia p95 maxima en segundos")
    args = parser.parse_args()

    print(f"Ejecutando reliability test durante {args.duration}s contra {SERVICE_URL}/health ...")
    metrics = run_reliability_test(args.duration, args.interval)

    if metrics["total"] == 0:
        print("No se registraron peticiones")
        sys.exit(1)

    success_rate = metrics["success"] / metrics["total"]
    latencies_sorted = sorted(metrics["latencies"])
    p95_index = max(0, int(len(latencies_sorted) * 0.95) - 1)
    p95_latency = latencies_sorted[p95_index]

    print(f"Peticiones totales : {metrics['total']}")
    print(f"Success rate       : {success_rate:.2%}")
    print(f"Latencia p95       : {p95_latency:.3f}s")

    failed = False
    if success_rate < args.slo_success_rate:
        print(f"FALLO: success rate {success_rate:.2%} por debajo del SLO {args.slo_success_rate:.2%}")
        failed = True

    if p95_latency > args.slo_latency:
        print(f"FALLO: latencia p95 {p95_latency:.3f}s supera el SLO {args.slo_latency:.3f}s")
        failed = True

    if failed:
        sys.exit(1)

    print("OK: el servicio cumple con los SLOs definidos")


if __name__ == "__main__":
    main()
