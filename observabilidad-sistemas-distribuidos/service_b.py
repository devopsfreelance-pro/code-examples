"""
service-b: servicio "downstream" que simula acceso a inventario.

Demuestra:
- Instrumentacion automatica de FastAPI con OpenTelemetry (crea spans por request).
- Extraccion del trace_id del span activo para usarlo como correlation ID en logs.
- Exportacion de trazas via OTLP/HTTP hacia Jaeger.
"""
import logging
import os
import random
import time

import uvicorn
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", "service-b")
OTLP_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")

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

app = FastAPI(title="service-b")
FastAPIInstrumentor.instrument_app(app)


def correlation_id() -> str:
    """Usa el trace_id del span activo como correlation ID para los logs."""
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx and ctx.trace_id:
        return format(ctx.trace_id, "032x")
    return "no-trace"


@app.get("/health")
def health():
    return {"status": "ok", "service": SERVICE_NAME}


@app.get("/inventory/{sku}")
def check_inventory(sku: str):
    cid = correlation_id()
    logger.info("correlation_id=%s recibida consulta de inventario sku=%s", cid, sku)

    with tracer.start_as_current_span("check-warehouse-stock") as span:
        span.set_attribute("app.sku", sku)
        # Simula latencia variable de una consulta a base de datos.
        delay = random.uniform(0.05, 0.25)
        time.sleep(delay)
        span.set_attribute("app.query_duration_ms", round(delay * 1000, 2))

        available = random.choice([True, True, False])
        span.set_attribute("app.stock_available", available)

    logger.info(
        "correlation_id=%s sku=%s stock_available=%s duracion_ms=%.2f",
        cid, sku, available, delay * 1000,
    )
    return {"sku": sku, "available": available, "correlation_id": cid}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
