#!/usr/bin/env python3
"""
Mini benchmark HTTP para comparar el rendimiento de dos servidores Nginx:
uno con parametros de red por defecto y otro con tuning de kernel aplicado
(net.core.somaxconn, net.ipv4.tcp_fin_timeout), tal como se describe en el
post "Optimizar servidor: Técnicas probadas de rendimiento 2025".

No usa dependencias externas, solo la librería estándar de Python 3.
"""

import argparse
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


def do_request(url: str) -> float:
    start = time.perf_counter()
    with urllib.request.urlopen(url, timeout=5) as response:
        response.read()
    return time.perf_counter() - start


def run_benchmark(url: str, total_requests: int, concurrency: int) -> None:
    latencies = []
    errors = 0

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(do_request, url) for _ in range(total_requests)]
        for future in as_completed(futures):
            try:
                latencies.append(future.result())
            except (urllib.error.URLError, OSError):
                errors += 1
    elapsed = time.perf_counter() - start

    print(f"URL objetivo:        {url}")
    print(f"Requests totales:    {total_requests}")
    print(f"Concurrencia:        {concurrency}")
    print(f"Errores:             {errors}")
    print(f"Tiempo total:        {elapsed:.2f} s")

    if latencies:
        ok = len(latencies)
        rps = ok / elapsed if elapsed > 0 else 0
        avg_ms = statistics.mean(latencies) * 1000
        p95_ms = statistics.quantiles(latencies, n=100)[94] * 1000 if ok >= 20 else max(latencies) * 1000
        print(f"Requests/segundo:    {rps:.1f}")
        print(f"Latencia promedio:   {avg_ms:.2f} ms")
        print(f"Latencia p95:        {p95_ms:.2f} ms")
    else:
        print("No se completo ningun request exitoso.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, required=True, help="Puerto local del servidor Nginx (8081 baseline, 8082 tuned)")
    parser.add_argument("--host", default="localhost", help="Host del servidor (default: localhost)")
    parser.add_argument("--requests", type=int, default=2000, help="Cantidad total de requests (default: 2000)")
    parser.add_argument("--concurrency", type=int, default=100, help="Requests concurrentes (default: 100)")
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}/"
    run_benchmark(url, args.requests, args.concurrency)
    return 0


if __name__ == "__main__":
    sys.exit(main())
