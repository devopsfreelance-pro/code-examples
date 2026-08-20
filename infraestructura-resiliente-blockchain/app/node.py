"""
Simula un nodo blockchain minimo: expone su identidad, un "block_height"
que avanza solo, y un endpoint /health para que el balanceador y los
healthchecks de Docker puedan detectar si el nodo esta caido.
"""
import os
import threading
import time
from datetime import datetime, timezone

from flask import Flask, jsonify

app = Flask(__name__)

NODE_ID = os.environ.get("NODE_ID", "node-unknown")
BLOCK_INTERVAL_SECONDS = float(os.environ.get("BLOCK_INTERVAL_SECONDS", "2"))

state = {"block_height": 0}
state_lock = threading.Lock()


def mine_blocks():
    while True:
        time.sleep(BLOCK_INTERVAL_SECONDS)
        with state_lock:
            state["block_height"] += 1


@app.route("/")
def status():
    with state_lock:
        block_height = state["block_height"]
    return jsonify(
        {
            "node": NODE_ID,
            "block_height": block_height,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok", "node": NODE_ID}), 200


if __name__ == "__main__":
    miner_thread = threading.Thread(target=mine_blocks, daemon=True)
    miner_thread.start()
    app.run(host="0.0.0.0", port=5000)
