#!/usr/bin/env python3
"""
Exportador Prometheus simulado para validadores de Ethereum (consenso PoS).

Basado en el ejemplo del post "Guía Completa de Monitoreo de consenso en
Ethereum": expone las mismas metricas (balance, estado, efectividad de
attestation) que el script real del post, pero en vez de consultar un
nodo Beacon real (http://localhost:5052) genera datos simulados para que
el ejemplo corra standalone, sin necesidad de sincronizar un nodo Ethereum.
"""
import logging
import random
import time

from prometheus_client import start_http_server, Gauge

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("eth-validator-exporter")

# Mismas metricas que describe el post
validator_balance = Gauge(
    "validator_balance", "Current validator balance in Gwei", ["validator_index"]
)
validator_status = Gauge(
    "validator_status",
    "Validator status (0=pending, 1=active, 2=exiting)",
    ["validator_index"],
)
attestation_effectiveness = Gauge(
    "attestation_effectiveness",
    "Percentage of successful attestations",
    ["validator_index"],
)
validator_missed_attestations_total = Gauge(
    "validator_missed_attestations_total",
    "Total missed attestations (contador simulado, no counter real)",
    ["validator_index"],
)

# Simulamos 3 validadores, igual que el ejemplo del post
VALIDATOR_INDICES = [123456, 123457, 123458]

# Estado inicial simulado por validador
_state = {
    idx: {
        "balance": 32_000_000_000 + random.randint(-500_000, 500_000),
        "status": 1,  # activo
        "missed": 0,
    }
    for idx in VALIDATOR_INDICES
}

# El validador 123458 se simula "problemático" para poder ver la alerta
# ValidatorMissedAttestation disparándose en Prometheus/Alertmanager.
PROBLEM_VALIDATOR = 123458


def simulate_tick():
    for idx in VALIDATOR_INDICES:
        st = _state[idx]

        if idx == PROBLEM_VALIDATOR:
            # Este validador falla attestations la mayoria de los ticks
            missed_this_tick = random.random() < 0.7
        else:
            # El resto falla muy ocasionalmente
            missed_this_tick = random.random() < 0.02

        if missed_this_tick:
            st["missed"] += 1
            effectiveness = max(0, 100 - st["missed"] * 5)
        else:
            effectiveness = min(100, 95 + random.random() * 5)
            st["balance"] += random.randint(0, 20)  # recompensa pequeña

        validator_balance.labels(validator_index=idx).set(st["balance"])
        validator_status.labels(validator_index=idx).set(st["status"])
        attestation_effectiveness.labels(validator_index=idx).set(effectiveness)
        validator_missed_attestations_total.labels(validator_index=idx).set(st["missed"])

        logger.info(
            "Validator %s - Balance: %s Gwei, Missed: %s, Effectiveness: %.1f%%",
            idx,
            st["balance"],
            st["missed"],
            effectiveness,
        )


if __name__ == "__main__":
    start_http_server(8081)
    logger.info("Exportador escuchando en :8081/metrics")
    while True:
        simulate_tick()
        time.sleep(15)
