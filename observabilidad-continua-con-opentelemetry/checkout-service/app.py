"""
Servicio de checkout.

Llama al coupon-service via HTTP. La instrumentacion automatica de
`requests` propaga el contexto de traza (traceparent) en el header saliente,
y la de Flask lo recibe del lado del coupon-service: asi ambos spans quedan
correlacionados en una unica traza distribuida, sin escribir codigo de
propagacion a mano.
"""

import os

import requests
from flask import Flask, jsonify, request

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

COLLECTOR_ENDPOINT = os.environ.get("OTEL_COLLECTOR_ENDPOINT", "otel-collector:4317")
COUPON_SERVICE_URL = os.environ.get("COUPON_SERVICE_URL", "http://coupon-service:5001")

resource = Resource.create(
    {
        "service.name": "checkout-service",
        "service.version": "1.0.0",
        "deployment.environment": "demo",
    }
)

trace_provider = TracerProvider(resource=resource)
span_exporter = OTLPSpanExporter(endpoint=COLLECTOR_ENDPOINT, insecure=True)
trace_provider.add_span_processor(BatchSpanProcessor(span_exporter))
trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer("checkout-service")

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()


@app.route("/checkout")
def checkout():
    codigos = request.args.get("cupones", "")

    with tracer.start_as_current_span("checkout") as span:
        span.set_attribute("checkout.cupones", codigos)

        resp = requests.get(
            f"{COUPON_SERVICE_URL}/validar-cupones",
            params={"codigos": codigos},
            timeout=10,
        )
        resp.raise_for_status()
        resultado = resp.json()

        span.set_attribute("checkout.cupones_validados", len(resultado["cupones_validados"]))

    return jsonify({"checkout": "aprobado", **resultado})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
