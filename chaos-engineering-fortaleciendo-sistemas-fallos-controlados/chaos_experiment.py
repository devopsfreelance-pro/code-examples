#!/usr/bin/env python3
"""
Mini-experimento de Chaos Engineering (estilo Chaos Monkey) contra el
"payment-service" definido en docker-compose.yml.

Reproduce, de forma ejecutable, la misma estructura de tres pasos que
aparece en el post:

  1. hypothesis_steady_state() - confirma el estado estable (99.9%+ de
     disponibilidad con las 3 instancias arriba).
  2. inject_failure()          - termina aleatoriamente una instancia del
     servicio, igual que Chaos Monkey terminaba instancias de EC2.
  3. verify_recovery()         - valida que el sistema se recupera solo
     (gracias a `restart: unless-stopped` en docker-compose.yml) sin
     intervencion humana.

Solo usa la libreria estandar de Python y el CLI de docker.
"""
import json
import random
import subprocess
import sys
import time
import urllib.request

SERVICE_PORTS = [8081, 8082, 8083]
CHAOS_LABEL = "chaos.target=payment-service"
HEALTH_TIMEOUT = 2
RECOVERY_WAIT_SECONDS = 8


def get_target_containers():
    """Lista los contenedores etiquetados como blanco del experimento."""
    result = subprocess.run(
        ["docker", "ps", "--filter", f"label={CHAOS_LABEL}", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
        check=True,
    )
    names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not names:
        print("ERROR: no se encontraron contenedores con label "
              f"'{CHAOS_LABEL}'. Corre 'docker compose up -d' primero.")
        sys.exit(1)
    return names


def check_instance_health(port):
    """Devuelve True si la instancia en ese puerto responde 200 en /health."""
    try:
        with urllib.request.urlopen(
            f"http://localhost:{port}/health", timeout=HEALTH_TIMEOUT
        ) as response:
            return response.status == 200
    except Exception:
        return False


def measure_availability():
    """Fraccion de instancias del payment-service que estan saludables."""
    healthy = sum(check_instance_health(port) for port in SERVICE_PORTS)
    return healthy / len(SERVICE_PORTS)


def hypothesis_steady_state():
    """
    Paso 1: verificar que el sistema mantiene el estado estable
    (las 3 instancias del payment-service disponibles) antes de
    inyectar ningun fallo.
    """
    print("=== 1. Hipotesis de estado estable ===")
    availability = measure_availability()
    print(f"Disponibilidad medida (baseline): {availability * 100:.1f}%")
    assert availability == 1.0, (
        f"Estado estable no confirmado: disponibilidad {availability} "
        "por debajo del 100% esperado. Verifica 'docker compose up -d'."
    )
    print("OK: estado estable confirmado (3/3 instancias saludables).\n")


def inject_failure():
    """
    Paso 2: terminar aleatoriamente una instancia del payment-service,
    igual que Chaos Monkey terminaba instancias de EC2 en Netflix.
    """
    print("=== 2. Inyeccion de fallo: terminar una instancia al azar ===")
    targets = get_target_containers()
    victim = random.choice(targets)
    subprocess.run(["docker", "kill", victim], check=True, capture_output=True)
    print(f"Instancia terminada: {victim}\n")
    return victim


def verify_recovery(victim):
    """
    Paso 3: esperar el periodo de recuperacion y validar que el sistema
    se recupero automaticamente (Docker reinicia el contenedor por la
    politica 'restart: unless-stopped', simulando el auto-healing de
    un orquestador real).
    """
    print(f"=== 3. Verificacion de recuperacion (esperando {RECOVERY_WAIT_SECONDS}s) ===")
    time.sleep(RECOVERY_WAIT_SECONDS)
    availability = measure_availability()
    print(f"Disponibilidad medida (post-recuperacion): {availability * 100:.1f}%")

    result = {
        "victim": victim,
        "availability_recovered": availability == 1.0,
        "availability_pct": round(availability * 100, 1),
    }
    return result


def main():
    hypothesis_steady_state()
    victim = inject_failure()
    result = verify_recovery(victim)

    print("\n=== Resultado del experimento ===")
    print(json.dumps(result, indent=2))

    if result["availability_recovered"]:
        print("\nOK: el sistema se recupero solo, sin intervencion humana.")
        sys.exit(0)
    else:
        print(
            "\nFALLO: el sistema no se recupero dentro del tiempo esperado. "
            "Esto es justamente lo que un experimento de chaos engineering "
            "esta pensado para revelar."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
