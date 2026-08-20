"""
Servicio de ejemplo para demostrar reliability testing.

Expone:
- GET  /health          -> health check normal del servicio protegido
- POST /admin/chaos     -> endpoint de administracion para inyectar fallos
                            (failure_rate, latency_ms), simulando un
                            experimento de chaos engineering en caliente.

El servicio arranca "sano" (failure_rate=0.0) y solo se degrada cuando
el script chaos_test.py llama al endpoint de administracion.
"""
import random
import time

from flask import Flask, jsonify, request

app = Flask(__name__)

state = {
    "failure_rate": 0.0,
    "latency_ms": 0,
}


@app.route("/health", methods=["GET"])
def health():
    if state["latency_ms"] > 0:
        time.sleep(state["latency_ms"] / 1000)

    if random.random() < state["failure_rate"]:
        return jsonify(status="error", detail="fallo inyectado"), 500

    return jsonify(status="ok"), 200


@app.route("/admin/chaos", methods=["POST"])
def chaos():
    payload = request.get_json(force=True, silent=True) or {}
    state["failure_rate"] = float(payload.get("failure_rate", state["failure_rate"]))
    state["latency_ms"] = int(payload.get("latency_ms", state["latency_ms"]))
    return jsonify(status="chaos-updated", state=state), 200


@app.route("/admin/reset", methods=["POST"])
def reset():
    state["failure_rate"] = 0.0
    state["latency_ms"] = 0
    return jsonify(status="reset", state=state), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
