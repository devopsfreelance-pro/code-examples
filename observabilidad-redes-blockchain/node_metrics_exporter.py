#!/usr/bin/env python3
"""
Exportador Prometheus simulado para un nodo de una red blockchain.

Expone metricas tipicas que un equipo de DevOps instrumentaria en un nodo
real (block height, peers conectados, tamano del mempool y latencia de
propagacion de bloques) para poder construir observabilidad sobre una red
blockchain, tal como describe el post "Observabilidad en redes blockchain".

Se ejecuta un nodo por contenedor. El comportamiento se controla con
variables de entorno para poder simular, sin tocar codigo, un nodo sano y
un nodo que se atrasa respecto al resto de la red (caso de uso central del
post: detectar anomalias de sincronizacion entre nodos).

Variables de entorno:
  NODE_ID        Identificador del nodo (ej: node-1). Default: "node-unknown".
  START_HEIGHT   Altura de bloque inicial. Default: 1000.
  BLOCK_INTERVAL Segundos entre bloques nuevos en condiciones normales. Default: 5.
  LAGGING        "true" para simular un nodo que se atrasa (deja de avanzar
                 bloques de forma intermitente). Default: "false".
  PORT           Puerto donde se expone /metrics. Default: 8000.
"""
import logging
import os
import random
import time

from prometheus_client import Gauge, start_http_server

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("blockchain-node-exporter")

NODE_ID = os.environ.get("NODE_ID", "node-unknown")
START_HEIGHT = int(os.environ.get("START_HEIGHT", "1000"))
BLOCK_INTERVAL = float(os.environ.get("BLOCK_INTERVAL", "5"))
LAGGING = os.environ.get("LAGGING", "false").lower() == "true"
PORT = int(os.environ.get("PORT", "8000"))

block_height = Gauge(
    "blockchain_node_block_height", "Altura de bloque actual del nodo", ["node_id"]
)
peer_count = Gauge(
    "blockchain_node_peer_count", "Cantidad de peers conectados", ["node_id"]
)
mempool_size = Gauge(
    "blockchain_node_mempool_size", "Transacciones pendientes en el mempool", ["node_id"]
)
block_propagation_seconds = Gauge(
    "blockchain_node_block_propagation_seconds",
    "Latencia estimada de propagacion del ultimo bloque recibido",
    ["node_id"],
)

_height = START_HEIGHT


def simulate_tick():
    global _height

    if LAGGING and random.random() < 0.6:
        # El nodo "problematico" se atrasa: no procesa bloque nuevo este tick.
        logger.warning("%s no proceso bloque nuevo (posible atraso de sync)", NODE_ID)
    else:
        _height += 1

    peers = random.randint(6, 12) if not LAGGING else random.randint(1, 4)
    mempool = random.randint(50, 400)
    propagation = round(random.uniform(0.2, 1.5) if not LAGGING else random.uniform(3.0, 8.0), 2)

    block_height.labels(node_id=NODE_ID).set(_height)
    peer_count.labels(node_id=NODE_ID).set(peers)
    mempool_size.labels(node_id=NODE_ID).set(mempool)
    block_propagation_seconds.labels(node_id=NODE_ID).set(propagation)

    logger.info(
        "%s height=%s peers=%s mempool=%s propagation=%.2fs",
        NODE_ID,
        _height,
        peers,
        mempool,
        propagation,
    )


if __name__ == "__main__":
    start_http_server(PORT)
    logger.info("%s exportando metricas en :%s/metrics (LAGGING=%s)", NODE_ID, PORT, LAGGING)
    while True:
        simulate_tick()
        time.sleep(BLOCK_INTERVAL)
