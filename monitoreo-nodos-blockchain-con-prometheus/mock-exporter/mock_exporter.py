#!/usr/bin/env python3
"""
mock_exporter.py - simula el endpoint de metricas Prometheus de un nodo
Ethereum (cliente de ejecucion + consenso), para poder probar el stack de
monitoreo del post sin levantar un nodo real.

Expone en /metrics las mismas metricas que se usan en las reglas de alerta
del post: ethereum_blockchain_height, chain_head_block, p2p_peers,
txpool_pending, beacon_head_slot, beacon_finalized_epoch.

Variables de entorno para forzar escenarios de alerta durante la demo:
  SIMULATE_OUT_OF_SYNC=1   -> chain_head_block queda 80 bloques atras
  SIMULATE_LOW_PEERS=1     -> p2p_peers cae a 2
  SIMULATE_MEMPOOL_FULL=1  -> txpool_pending sube a 15000
"""
import os
import random
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

NETWORK_HEIGHT_START = 21_000_000


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            return

        elapsed_blocks = int(time.time() - START_TIME) // 12  # ~12s por bloque
        network_height = NETWORK_HEIGHT_START + elapsed_blocks

        out_of_sync = os.environ.get("SIMULATE_OUT_OF_SYNC") == "1"
        low_peers = os.environ.get("SIMULATE_LOW_PEERS") == "1"
        mempool_full = os.environ.get("SIMULATE_MEMPOOL_FULL") == "1"

        lag = 80 if out_of_sync else random.randint(0, 2)
        head_block = network_height - lag
        peers = 2 if low_peers else random.randint(15, 40)
        pending_tx = 15000 if mempool_full else random.randint(50, 500)
        beacon_slot = elapsed_blocks
        beacon_finalized_epoch = max(0, (beacon_slot // 32) - 2)

        body = "\n".join([
            "# HELP ethereum_blockchain_height Altura de bloque conocida de la red",
            "# TYPE ethereum_blockchain_height gauge",
            f"ethereum_blockchain_height {network_height}",
            "# HELP chain_head_block Altura de bloque local del nodo",
            "# TYPE chain_head_block gauge",
            f"chain_head_block {head_block}",
            "# HELP p2p_peers Peers P2P conectados",
            "# TYPE p2p_peers gauge",
            f"p2p_peers {peers}",
            "# HELP txpool_pending Transacciones pendientes en el mempool",
            "# TYPE txpool_pending gauge",
            f"txpool_pending {pending_tx}",
            "# HELP beacon_head_slot Slot actual del beacon node",
            "# TYPE beacon_head_slot gauge",
            f"beacon_head_slot {beacon_slot}",
            "# HELP beacon_finalized_epoch Ultimo epoch finalizado",
            "# TYPE beacon_finalized_epoch gauge",
            f"beacon_finalized_epoch {beacon_finalized_epoch}",
            "",
        ])

        encoded = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args):
        return  # silenciar el log de acceso por request


START_TIME = time.time()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    server = HTTPServer(("0.0.0.0", port), MetricsHandler)
    print(f"mock-exporter escuchando en :{port}/metrics")
    server.serve_forever()
