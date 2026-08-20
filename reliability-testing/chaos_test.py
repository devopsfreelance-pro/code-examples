"""
Experimento de chaos engineering: inyecta una tasa de fallos alta en el
servicio via /admin/chaos y valida que un circuit breaker "cliente" se
active tras N fallos consecutivos, siguiendo el mismo patron que el
ejemplo de Chaos Toolkit del post (inject_latency_fault /
test_circuit_breaker_activation), pero contra un servicio real en
Docker en lugar de una funcion simulada.

Uso:
    python chaos_test.py --failure-rate 0.8 --latency-ms 200 --threshold 5
"""
import argparse
import sys

import requests

SERVICE_URL = "http://localhost:5000"


def set_chaos(failure_rate, latency_ms):
    response = requests.post(
        f"{SERVICE_URL}/admin/chaos",
        json={"failure_rate": failure_rate, "latency_ms": latency_ms},
        timeout=5,
    )
    response.raise_for_status()


def reset_chaos():
    requests.post(f"{SERVICE_URL}/admin/reset", timeout=5)


def circuit_breaker_trips(threshold, max_attempts=20):
    """
    Simula un circuit breaker "cliente": cuenta fallos consecutivos contra
    el servicio real y devuelve True si se alcanza el umbral antes de
    agotar los intentos.
    """
    consecutive_failures = 0

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(f"{SERVICE_URL}/health", timeout=5)
            if response.status_code == 200:
                consecutive_failures = 0
            else:
                consecutive_failures += 1
        except requests.exceptions.RequestException:
            consecutive_failures += 1

        print(f"Intento {attempt}: fallos consecutivos = {consecutive_failures}")

        if consecutive_failures >= threshold:
            return True

    return False


def main():
    parser = argparse.ArgumentParser(description="Chaos experiment con circuit breaker")
    parser.add_argument("--failure-rate", type=float, default=0.8)
    parser.add_argument("--latency-ms", type=int, default=0)
    parser.add_argument("--threshold", type=int, default=5)
    args = parser.parse_args()

    print(f"Inyectando fallos: failure_rate={args.failure_rate}, latency_ms={args.latency_ms}")
    set_chaos(args.failure_rate, args.latency_ms)

    try:
        tripped = circuit_breaker_trips(args.threshold)
    finally:
        print("Restaurando el servicio a estado sano...")
        reset_chaos()

    if tripped:
        print(f"OK: el circuit breaker se activo tras {args.threshold} fallos consecutivos")
        sys.exit(0)

    print(f"FALLO: no se alcanzaron {args.threshold} fallos consecutivos en el experimento")
    sys.exit(1)


if __name__ == "__main__":
    main()
