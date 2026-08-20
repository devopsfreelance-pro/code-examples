#!/usr/bin/env python3
"""
Aplicacion de ejemplo que simula los sintomas descritos en el post:
- Memory leak lento (una lista que crece y nunca se libera)
- Picos de CPU periodicos (calculo intensivo cada N segundos)
- Logs estructurados con niveles INFO/WARN/ERROR/CRITICAL para que
  se puedan practicar tecnicas de analisis de logs (grep/awk) similares
  a las del post con journalctl.
"""
import logging
import random
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s pid=%(process)d %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("leaky-app")

# Lista que crece indefinidamente: simula el memory leak.
_leak_buffer = []

REQUEST_TYPES = ["GET /api/orders", "POST /api/payments", "GET /api/health", "DELETE /api/cache"]


def cpu_burn(seconds: float) -> None:
    """Satura un nucleo de CPU durante 'seconds' para simular un pico de carga."""
    end = time.time() + seconds
    x = 0
    while time.time() < end:
        x += sum(i * i for i in range(1000))


def simulate_request() -> None:
    req = random.choice(REQUEST_TYPES)
    latency_ms = random.randint(5, 40)

    # Cada tanto la latencia se dispara y se registra como error/critico,
    # para poder practicar journalctl-style filtering (aca via docker logs).
    if random.random() < 0.12:
        latency_ms = random.randint(800, 3000)
        log.error("request=%s status=500 latency_ms=%d causa=timeout_backend", req, latency_ms)
    elif random.random() < 0.05:
        log.critical("request=%s status=503 latency_ms=%d causa=pool_conexiones_agotado", req, latency_ms)
    else:
        log.info("request=%s status=200 latency_ms=%d", req, latency_ms)


def main() -> None:
    log.info("leaky-app iniciada, PID=%d", __import__("os").getpid())
    tick = 0
    while True:
        # Memory leak: cada iteracion agrega ~50KB que nunca se libera.
        _leak_buffer.append(bytearray(50 * 1024))

        simulate_request()

        # Pico de CPU cada 15 iteraciones (~15s) para poder observarlo
        # con docker stats / top, igual que el analisis de perf del post.
        tick += 1
        if tick % 15 == 0:
            log.warning("iniciando tarea batch intensiva en CPU")
            cpu_burn(3.0)

        time.sleep(1)


if __name__ == "__main__":
    main()
