"""Servicio "order-service": punto de entrada de la traza distribuida.

Al llamar /process-payment, hace una peticion HTTP a payment-service.
La instrumentacion automatica de requests (RequestsInstrumentor)
propaga el contexto W3C Trace Context, por lo que ambos spans
aparecen conectados en una unica traza en Jaeger.
"""
import os

import requests
from flask import Flask, jsonify
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

from tracing_setup import setup_tracing

tracer = setup_tracing(service_name="order-service")

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

PAYMENT_SERVICE_URL = os.environ.get("PAYMENT_SERVICE_URL", "http://payment-service:5001")


@app.route("/process-payment")
def process_payment():
    with tracer.start_as_current_span("process-order-payment") as span:
        span.set_attribute("order.id", "order-12345")

        response = requests.get(f"{PAYMENT_SERVICE_URL}/validate-payment", timeout=5)
        result = response.json()

        span.set_attribute("order.payment_validated", result["validated"])

    return jsonify({"order_id": "order-12345", "payment": result})


@app.route("/")
def health():
    return jsonify({"status": "ok", "service": "order-service"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
