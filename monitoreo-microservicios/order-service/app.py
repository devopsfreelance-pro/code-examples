"""
order-service: microservicio "entrypoint" del ejemplo.

Expone:
  - GET /health/liveness   -> liveness probe
  - GET /health/readiness  -> readiness probe (con dependencia simulada)
  - GET /metrics           -> metricas RED en formato Prometheus
  - GET /order             -> endpoint de negocio: genera/propaga el
                               correlation ID, llama a inventory-service y
                               loguea todo el flujo en JSON
"""
import json
import logging
import sys
import time
import uuid

import requests
from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

SERVICE_NAME = "order-service"
INVENTORY_URL = "http://inventory-service:5001"

app = Flask(__name__)

# --- Logging estructurado en JSON con correlation ID ---
logger = logging.getLogger(SERVICE_NAME)
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(_handler)


def log_event(correlation_id, **fields):
    payload = {"service": SERVICE_NAME, "correlationId": correlation_id, **fields}
    logger.info(json.dumps(payload))


# --- Metricas RED (Rate, Errors, Duration) ---
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Cantidad total de solicitudes HTTP",
    ["method", "path", "status_code", "service"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Latencia de las solicitudes HTTP",
    ["method", "path", "service"],
)


@app.before_request
def start_timer():
    request.start_time = time.time()
    # Propaga el correlation ID entrante o genera uno nuevo (igual que el
    # middleware del post, adaptado de Express a Flask)
    request.correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))


@app.after_request
def record_metrics(response):
    duration = time.time() - request.start_time
    REQUEST_LATENCY.labels(request.method, request.path, SERVICE_NAME).observe(duration)
    REQUEST_COUNT.labels(
        request.method, request.path, response.status_code, SERVICE_NAME
    ).inc()
    response.headers["x-correlation-id"] = request.correlation_id
    return response


@app.route("/health/liveness")
def liveness():
    # Health check basico: el proceso esta vivo
    return jsonify({"status": "alive"}), 200


@app.route("/health/readiness")
def readiness():
    # Health check profundo: valida dependencias (inventory-service)
    checks = {"inventory_service": check_inventory_service()}
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    return jsonify({
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
    }), status_code


def check_inventory_service():
    try:
        resp = requests.get(f"{INVENTORY_URL}/health/liveness", timeout=2)
        return resp.status_code == 200
    except requests.RequestException:
        return False


@app.route("/order")
def create_order():
    order_id = str(uuid.uuid4())[:8]
    correlation_id = request.correlation_id

    log_event(correlation_id, event="order_received", order_id=order_id)

    # Propaga el correlation ID al llamar al siguiente servicio de la cadena
    inventory_resp = requests.get(
        f"{INVENTORY_URL}/inventory/check",
        params={"order_id": order_id},
        headers={"x-correlation-id": correlation_id},
        timeout=5,
    )
    inventory_data = inventory_resp.json()

    log_event(
        correlation_id,
        event="order_completed",
        order_id=order_id,
        inventory_available=inventory_data.get("available"),
    )

    return jsonify({
        "order_id": order_id,
        "correlation_id": correlation_id,
        "inventory": inventory_data,
        "status": "completed",
    })


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
