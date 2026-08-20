"""
Mock de un nodo blockchain (estilo Ethereum JSON-RPC) para demostrar
escalabilidad horizontal y balanceo de carga entre nodos de consulta.

Cada instancia expone:
  - POST /rpc   -> simula eth_blockNumber y net_peerCount (JSON-RPC 2.0)
  - GET  /health -> healthcheck simple (para NGINX / kubernetes probes)

Cada instancia arranca en una altura de bloque distinta y avanza sola,
simulando nodos reales que están todos sincronizados a la misma red pero
son procesos independientes. El NODE_ID (variable de entorno) permite ver
en las respuestas a qué nodo del pool respondió cada request.
"""

import os
import threading
import time

from flask import Flask, jsonify, request

app = Flask(__name__)

NODE_ID = os.environ.get("NODE_ID", "node-unknown")
START_BLOCK = int(os.environ.get("START_BLOCK", "18000000"))

state = {
    "block_height": START_BLOCK,
    "peer_count": 12,
    "requests_served": 0,
}
state_lock = threading.Lock()


def advance_chain():
    """Simula la llegada de nuevos bloques cada ~12s (tiempo real de Ethereum)."""
    while True:
        time.sleep(12)
        with state_lock:
            state["block_height"] += 1


threading.Thread(target=advance_chain, daemon=True).start()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "node_id": NODE_ID}), 200


@app.route("/rpc", methods=["POST"])
def rpc():
    payload = request.get_json(force=True, silent=True) or {}
    method = payload.get("method", "")
    req_id = payload.get("id", 1)

    with state_lock:
        state["requests_served"] += 1
        block_height = state["block_height"]
        peer_count = state["peer_count"]
        served = state["requests_served"]

    if method == "eth_blockNumber":
        result = hex(block_height)
    elif method == "net_peerCount":
        result = hex(peer_count)
    else:
        return (
            jsonify(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Método no soportado en el mock: {method}"},
                }
            ),
            400,
        )

    response = jsonify(
        {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result,
            "_served_by": NODE_ID,
            "_requests_served_by_this_node": served,
        }
    )
    response.headers["X-Node-Id"] = NODE_ID
    return response, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8545)
