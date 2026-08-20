"""
Compara la latencia de N invocaciones bajo los dos modelos de ejecución:

  - Contenedor: proceso persistente (app.py, ya levantado vía docker compose),
    se le hacen N requests HTTP reutilizando siempre el mismo proceso "warm".

  - Serverless (simulado): serverless_sim.py se ejecuta como subproceso nuevo
    en cada invocación, replicando el arranque desde cero de un cold start.

Uso:
    python3 benchmark.py [N]
"""
import json
import subprocess
import sys
import time
import urllib.request

CONTAINER_URL = "http://localhost:8000/process?text=hola+mundo+desde+devopsfreelance"
SERVERLESS_SCRIPT = "serverless_sim.py"


def benchmark_container(n: int) -> list:
    latencies = []
    for _ in range(n):
        start = time.perf_counter()
        with urllib.request.urlopen(CONTAINER_URL, timeout=5) as resp:
            resp.read()
        latencies.append((time.perf_counter() - start) * 1000)
    return latencies


def benchmark_serverless(n: int) -> list:
    latencies = []
    for _ in range(n):
        start = time.perf_counter()
        result = subprocess.run(
            [sys.executable, SERVERLESS_SCRIPT, "hola mundo desde devopsfreelance"],
            capture_output=True,
            text=True,
            check=True,
        )
        json.loads(result.stdout)  # valida que la respuesta es válida
        latencies.append((time.perf_counter() - start) * 1000)
    return latencies


def summarize(name: str, latencies: list) -> None:
    avg = sum(latencies) / len(latencies)
    print(f"{name}:")
    print(f"  invocaciones : {len(latencies)}")
    print(f"  promedio     : {avg:.2f} ms")
    print(f"  min / max    : {min(latencies):.2f} ms / {max(latencies):.2f} ms")
    print()


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20

    print(f"Ejecutando benchmark con {n} invocaciones por modelo...\n")

    try:
        container_latencies = benchmark_container(n)
    except Exception as exc:
        print("ERROR: no se pudo contactar al contenedor en localhost:8000.")
        print("¿Corriste 'docker compose up -d --build' antes de este script?")
        print(f"Detalle: {exc}")
        sys.exit(1)

    serverless_latencies = benchmark_serverless(n)

    summarize("Contenedor (proceso persistente, warm)", container_latencies)
    summarize("Serverless simulado (proceso nuevo por invocación)", serverless_latencies)

    diff = (
        sum(serverless_latencies) / len(serverless_latencies)
    ) / (sum(container_latencies) / len(container_latencies))
    print(
        f"El modelo serverless simulado fue en promedio {diff:.1f}x más lento "
        "por invocación debido al costo de arrancar un proceso nuevo cada vez "
        "(análogo al cold start de Lambda)."
    )


if __name__ == "__main__":
    main()
