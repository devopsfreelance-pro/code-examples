#!/usr/bin/env python3
"""
Exporter simulado que expone en formato Prometheus las metricas de un nodo
blockchain, usadas en el post como base para el pipeline de metricas:
- chain_transactions_total  -> TPS (sum(rate(...[5m])))
- beacon_head_slot / beacon_finalized_epoch -> finality time
- validator_attestation_hit_percentage / inclusion_distance -> attestation effectiveness
- node_filesystem_avail_bytes / size_bytes -> capacity planning / disk usage

No requiere dependencias externas, solo la libreria estandar de Python.
"""
import http.server
import random
import time

NODE_ID = "node-01"
REGION = "us-east-1"
CLIENT = "geth"

START = time.time()

# Estado simulado que avanza en cada scrape
state = {
    "tx_total": 1_500_000,
    "beacon_head_slot": 9_600_032,
    "beacon_finalized_epoch": 300_000,
    "disk_size_bytes": 2_000_000_000_000,  # 2 TB
    "disk_avail_bytes": 500_000_000_000,   # 500 GB libres
}


def advance_state():
    # ~15 transacciones por segundo desde el ultimo scrape (aprox)
    state["tx_total"] += random.randint(10, 20)
    state["beacon_head_slot"] += random.randint(1, 3)
    # la red finaliza cada 2 epochs en condiciones normales
    if random.random() < 0.3:
        state["beacon_finalized_epoch"] += 1
    # el disco crece de a poco (simula el crecimiento mensual del post)
    state["disk_avail_bytes"] = max(
        0, state["disk_avail_bytes"] - random.randint(0, 50_000_000)
    )


def render_metrics() -> str:
    advance_state()
    attestation_hit_pct = round(random.uniform(94.0, 99.5), 2)
    inclusion_distance = round(random.uniform(1.0, 2.5), 2)

    labels = f'node_id="{NODE_ID}",region="{REGION}",client="{CLIENT}"'

    lines = [
        "# HELP chain_transactions_total Total de transacciones incluidas en bloques",
        "# TYPE chain_transactions_total counter",
        f'chain_transactions_total{{{labels}}} {state["tx_total"]}',

        "# HELP beacon_head_slot Slot actual de la beacon chain",
        "# TYPE beacon_head_slot gauge",
        f'beacon_head_slot{{{labels}}} {state["beacon_head_slot"]}',

        "# HELP beacon_finalized_epoch Ultimo epoch finalizado",
        "# TYPE beacon_finalized_epoch gauge",
        f'beacon_finalized_epoch{{{labels}}} {state["beacon_finalized_epoch"]}',

        "# HELP validator_attestation_hit_percentage Porcentaje de atestaciones incluidas",
        "# TYPE validator_attestation_hit_percentage gauge",
        f'validator_attestation_hit_percentage{{{labels}}} {attestation_hit_pct}',

        "# HELP validator_attestation_inclusion_distance Distancia promedio de inclusion",
        "# TYPE validator_attestation_inclusion_distance gauge",
        f'validator_attestation_inclusion_distance{{{labels}}} {inclusion_distance}',

        "# HELP node_filesystem_size_bytes Tamano total del filesystem de datos",
        "# TYPE node_filesystem_size_bytes gauge",
        f'node_filesystem_size_bytes{{{labels},mountpoint="/data"}} {state["disk_size_bytes"]}',

        "# HELP node_filesystem_avail_bytes Espacio disponible en el filesystem de datos",
        "# TYPE node_filesystem_avail_bytes gauge",
        f'node_filesystem_avail_bytes{{{labels},mountpoint="/data"}} {state["disk_avail_bytes"]}',

        "# HELP p2p_peers Cantidad de peers conectados",
        "# TYPE p2p_peers gauge",
        f'p2p_peers{{{labels}}} {random.randint(20, 40)}',
    ]
    return "\n".join(lines) + "\n"


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/metrics", "/debug/metrics/prometheus"):
            body = render_metrics().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        pass  # silencia el log de acceso, ruidoso para un mock


if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", 8000), Handler)
    print("mock blockchain exporter escuchando en :8000/metrics")
    server.serve_forever()
