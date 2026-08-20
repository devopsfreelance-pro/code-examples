"""
Servicio de validacion de cupones.

Reproduce el caso real del post "OpenTelemetry: Guia Practica de
Observabilidad Continua": el p95 de latencia se dispara cuando un pedido
trae multiples cupones aplicados, y ese patron solo se detecta mirando
trazas individuales, no promedios agregados.
"""

import os
import time

from flask import Flask, jsonify, request

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

COLLECTOR_ENDPOINT = os.environ.get("OTEL_COLLECTOR_ENDPOINT", "otel-collector:4317")

resource = Resource.create(
    {
        "service.name": "coupon-service",
        "service.version": "1.0.0",
        "deployment.environment": "demo",
    }
)

trace_provider = TracerProvider(resource=resource)
span_exporter = OTLPSpanExporter(endpoint=COLLECTOR_ENDPOINT, insecure=True)
trace_provider.add_span_processor(BatchSpanProcessor(span_exporter))
trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer("coupon-service")

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()


def validar_un_cupon(codigo):
    # Cada validacion de cupon (contra un servicio de reglas de negocio,
    # DB, etc.) toma un tiempo fijo. Con pocos cupones no se nota; con
    # muchos, se acumula y explica el p95 alto del checkout.
    with tracer.start_as_current_span("validar-cupon") as span:
        span.set_attribute("cupon.codigo", codigo)
        time.sleep(0.3)


@app.route("/validar-cupones")
def validar_cupones():
    codigos = request.args.get("codigos", "")
    lista = [c for c in codigos.split(",") if c]

    span = trace.get_current_span()
    span.set_attribute("cupones.cantidad", len(lista))

    for codigo in lista:
        validar_un_cupon(codigo)

    return jsonify({"cupones_validados": lista, "todos_validos": True})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
