"""Inicializacion comun de OpenTelemetry para los microservicios de ejemplo.

Basado en el snippet de instrumentacion del post de observabilidad:
cada servicio configura su propio Resource (service.name) y exporta
las trazas via OTLP/gRPC al OpenTelemetry Collector.
"""
import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_tracing(service_name: str, service_version: str = "1.0.0") -> trace.Tracer:
    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "otel-collector:4317")

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
            "deployment.environment": "local-demo",
        }
    )

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)
