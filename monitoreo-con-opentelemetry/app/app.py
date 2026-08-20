"""
Mini API de pedidos instrumentada con OpenTelemetry.

Reproduce el ejemplo de instrumentacion manual del post "Guia Completa de
Monitoreo con OpenTelemetry": crea spans anidados (procesar-pedido >
validar-pedido / procesar-pago), agrega atributos y emite una metrica de
negocio (pedidos_procesados_total). Traces y metrics se exportan via OTLP
gRPC al OpenTelemetry Collector.
"""

import os
import random
import time

from flask import Flask, jsonify

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

COLLECTOR_ENDPOINT = os.environ.get("OTEL_COLLECTOR_ENDPOINT", "otel-collector:4317")

resource = Resource.create(
    {
        "service.name": "mi-api-pedidos",
        "service.version": "1.2.0",
        "deployment.environment": "demo",
    }
)

# --- Trazas ---
trace_provider = TracerProvider(resource=resource)
span_exporter = OTLPSpanExporter(endpoint=COLLECTOR_ENDPOINT, insecure=True)
trace_provider.add_span_processor(BatchSpanProcessor(span_exporter))
trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer("mi-api-pedidos")

# --- Metricas ---
metric_exporter = OTLPMetricExporter(endpoint=COLLECTOR_ENDPOINT, insecure=True)
metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter("mi-api-pedidos")
pedidos_counter = meter.create_counter(
    name="pedidos_procesados_total",
    description="Cantidad de pedidos procesados",
)

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)


class ResultadoPago:
    def __init__(self, estado):
        self.estado = estado


def validar(pedido_id):
    time.sleep(0.02)


def cobrar(pedido_id):
    time.sleep(random.uniform(0.05, 0.2))
    return ResultadoPago(estado="aprobado")


@app.route("/pedido/<pedido_id>")
def procesar_pedido(pedido_id):
    with tracer.start_as_current_span("procesar-pedido") as span:
        span.set_attribute("pedido.id", pedido_id)
        span.set_attribute("pedido.tipo", "ecommerce")

        with tracer.start_as_current_span("validar-pedido"):
            validar(pedido_id)

        with tracer.start_as_current_span("procesar-pago") as pago_span:
            resultado = cobrar(pedido_id)
            pago_span.set_attribute("pago.estado", resultado.estado)

        pedidos_counter.add(1, {"pedido.tipo": "ecommerce"})
        span.set_status(trace.StatusCode.OK)

    return jsonify({"pedido_id": pedido_id, "estado": resultado.estado})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
