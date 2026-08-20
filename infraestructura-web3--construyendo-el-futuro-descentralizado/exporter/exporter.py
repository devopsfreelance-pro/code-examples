"""
web3-exporter: consulta un nodo Ethereum (JSON-RPC) periodicamente y expone
metricas en formato Prometheus. Version minima del stack de monitoreo Web3
descripto en el post "Infraestructura Web3: Construyendo el Futuro
Descentralizado" (RPC + metrics.port + Prometheus scrape).
"""

import os
import time

import requests
from prometheus_client import Gauge, start_http_server

RPC_URL = os.environ.get("RPC_URL", "http://localhost:8545")
SCRAPE_INTERVAL = int(os.environ.get("SCRAPE_INTERVAL", "5"))
METRICS_PORT = int(os.environ.get("METRICS_PORT", "9100"))

block_number = Gauge("web3_block_number", "Ultimo numero de bloque visto en el nodo")
chain_id = Gauge("web3_chain_id", "Chain ID reportado por el nodo")
peer_count = Gauge("web3_peer_count", "Cantidad de peers conectados al nodo")
rpc_up = Gauge("web3_rpc_up", "1 si el endpoint JSON-RPC responde, 0 si no")


def rpc_call(method, params=None):
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}
    resp = requests.post(RPC_URL, json=payload, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data["result"]


def poll():
    try:
        bn = int(rpc_call("eth_blockNumber"), 16)
        cid = int(rpc_call("eth_chainId"), 16)
        try:
            peers = int(rpc_call("net_peerCount"), 16)
        except Exception:
            # Anvil no siempre implementa net_peerCount, no es critico
            peers = 0

        block_number.set(bn)
        chain_id.set(cid)
        peer_count.set(peers)
        rpc_up.set(1)
        print(f"[exporter] bloque={bn} chainId={cid} peers={peers}")
    except Exception as exc:  # noqa: BLE001 - queremos capturar cualquier fallo de red/RPC
        rpc_up.set(0)
        print(f"[exporter] error consultando {RPC_URL}: {exc}")


if __name__ == "__main__":
    start_http_server(METRICS_PORT)
    print(
        f"[exporter] sirviendo metricas en :{METRICS_PORT}, "
        f"consultando {RPC_URL} cada {SCRAPE_INTERVAL}s"
    )
    while True:
        poll()
        time.sleep(SCRAPE_INTERVAL)
