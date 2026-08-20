"""
Servicio de pagos de juguete para el game day.

Expone:
  GET /pay        -> simula el procesamiento de un pago (puede fallar por timeout
                      si el servicio externo se cae, ver /toggle-dependency)
  GET /health      -> healthcheck simple
  GET /metrics     -> métricas Prometheus (requests y latencia)
  POST /toggle-dependency -> simula que el "proveedor de pagos externo" empieza
                      a responder lento/con errores (esto es lo que Pumba/Chaos
                      Mesh harían inyectando latencia de red real; acá lo simulamos
                      en código para no depender de infraestructura extra)
"""
import random
import time

from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Mismo patrón de instrumentación que se describe en el post.
game_day_requests = Counter(
    "game_day_requests_total",
    "Total requests during game day",
    ["service", "endpoint", "status"],
)

game_day_latency = Histogram(
    "game_day_request_duration_seconds",
    "Request latency during game day",
    ["service", "endpoint"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)

# Estado global mutable: simula la salud del proveedor de pagos externo.
# degraded=False -> respuestas rápidas y confiables.
# degraded=True  -> latencia alta y errores intermitentes (fallo inyectado).
DEPENDENCY_STATE = {"degraded": False}


def call_external_payment_provider():
    """Simula la llamada al proveedor de pagos externo."""
    if DEPENDENCY_STATE["degraded"]:
        time.sleep(random.uniform(2.0, 4.0))
        if random.random() < 0.4:
            raise TimeoutError("proveedor de pagos externo no responde")
    else:
        time.sleep(random.uniform(0.02, 0.08))
    return {"authorized": True}


@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/pay")
def pay():
    service = "payment-service"
    endpoint = "/pay"
    start_time = time.time()
    try:
        result = call_external_payment_provider()
        game_day_requests.labels(service=service, endpoint=endpoint, status="success").inc()
        return jsonify(result)
    except Exception as exc:
        game_day_requests.labels(service=service, endpoint=endpoint, status="error").inc()
        return jsonify(error=str(exc)), 504
    finally:
        duration = time.time() - start_time
        game_day_latency.labels(service=service, endpoint=endpoint).observe(duration)


@app.route("/toggle-dependency", methods=["POST"])
def toggle_dependency():
    """Endpoint usado por el script del game day para inyectar/revertir el fallo."""
    degraded = request.args.get("degraded", "true").lower() == "true"
    DEPENDENCY_STATE["degraded"] = degraded
    return jsonify(degraded=DEPENDENCY_STATE["degraded"])


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
