"""
service-a: servicio "upstream" que atiende checkouts y llama a service-b.

Demuestra:
- Propagacion de contexto de traza (context propagation) entre servicios via
  headers HTTP (traceparent), usando la instrumentacion automatica de `requests`.
- Un unico trace_id conectando spans de dos servicios distintos: eso es lo que
  se ve como una sola traza en la UI de Jaeger.
- El mismo trace_id se usa como correlation ID en los logs de ambos servicios.
"""
import logging
import os

import requests
import uvicorn
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", "service-a")
OTLP_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
SERVICE_B_URL = os.environ.get("SERVICE_B_URL", "http://localhost:8001")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s level=%(levelname)s service=" + SERVICE_NAME + " %(message)s",
)
logger = logging.getLogger(SERVICE_NAME)

# --- Configuracion de tracing distribuido (OpenTelemetry) ---
provider = TracerProvider(resource=Resource.create({"service.name": SERVICE_NAME}))
exporter = OTLPSpanExporter(endpoint=f"{OTLP_ENDPOINT}/v1/traces")
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(SERVICE_NAME)

app = FastAPI(title="service-a")
FastAPIInstrumentor.instrument_app(app)
# Instrumenta la libreria `requests` para que propague automaticamente el
# header `traceparent` en cada llamada saliente hacia service-b.
RequestsInstrumentor().instrument()


def correlation_id() -> str:
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx and ctx.trace_id:
        return format(ctx.trace_id, "032x")
    return "no-trace"


@app.get("/health")
def health():
    return {"status": "ok", "service": SERVICE_NAME}


@app.get("/checkout/{sku}")
def checkout(sku: str):
    cid = correlation_id()
    logger.info("correlation_id=%s inicia checkout sku=%s", cid, sku)

    with tracer.start_as_current_span("validate-order") as span:
        span.set_attribute("app.sku", sku)
        # El header traceparent se inyecta automaticamente en esta llamada
        # gracias a RequestsInstrumentor, propagando el mismo trace_id.
        response = requests.get(f"{SERVICE_B_URL}/inventory/{sku}", timeout=5)
        response.raise_for_status()
        inventory = response.json()
        span.set_attribute("app.stock_available", inventory["available"])

    if not inventory["available"]:
        logger.warning("correlation_id=%s sku=%s sin stock, checkout rechazado", cid, sku)
        return {"correlation_id": cid, "sku": sku, "status": "rejected", "reason": "out_of_stock"}

    logger.info("correlation_id=%s sku=%s checkout confirmado", cid, sku)
    return {"correlation_id": cid, "sku": sku, "status": "confirmed"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
