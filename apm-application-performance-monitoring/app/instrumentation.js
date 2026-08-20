// Instrumentacion automatica con OpenTelemetry.
// Debe cargarse ANTES que cualquier otro modulo (ver "node -r ./instrumentation.js" en Dockerfile).
'use strict';

const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');

const traceExporter = new OTLPTraceExporter({
  // Jaeger acepta OTLP/HTTP en el puerto 4318 (endpoint /v1/traces)
  url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://jaeger:4318/v1/traces',
});

const sdk = new NodeSDK({
  serviceName: process.env.OTEL_SERVICE_NAME || 'apm-demo-app',
  traceExporter,
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();

process.on('SIGTERM', () => {
  sdk.shutdown().finally(() => process.exit(0));
});
