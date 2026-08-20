"""
inventory-service: microservicio downstream del ejemplo.

Expone:
  - GET /health/liveness   -> liveness probe
  - GET /health/readiness  -> readiness probe (con dependencia simulada)
  - GET /metrics           -> metricas RED en formato Prometheus
  - GET /inventory/check   -> endpoint de negocio, recibe el correlation ID
                               propagado por order-service y lo loguea en JSON
"""
import json
import logging
import sys
import time
import uuid

from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

SERVICE_NAME = "inventory-service"

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
    # Health check profundo: valida dependencias (simulado)
    checks = {"stock_database": True}
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    return jsonify({
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
    }), status_code


@app.route("/inventory/check")
def check_inventory():
    order_id = request.args.get("order_id", "unknown")
    log_event(
        request.correlation_id,
        event="inventory_check",
        order_id=order_id,
    )
    # Simula la consulta de stock
    available = True
    return jsonify({"order_id": order_id, "available": available})


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
