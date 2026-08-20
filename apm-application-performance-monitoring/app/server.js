'use strict';

// La instrumentacion se carga con "node -r ./instrumentation.js server.js" (ver Dockerfile),
// asi que aca ya esta activa cuando arranca Express.
const express = require('express');
const client = require('prom-client');
const { trace } = require('@opentelemetry/api');

const app = express();
const PORT = process.env.PORT || 3000;

// --- Metricas Prometheus (pilar "monitoreo de infraestructura y servicios") ---
const register = new client.Registry();
client.collectDefaultMetrics({ register });

const httpRequestDuration = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duracion de requests HTTP en segundos',
  labelNames: ['route', 'method', 'status_code'],
  buckets: [0.01, 0.05, 0.1, 0.3, 0.5, 1, 2, 5],
});
register.registerMetric(httpRequestDuration);

app.use((req, res, next) => {
  const end = httpRequestDuration.startTimer();
  res.on('finish', () => {
    end({ route: req.path, method: req.method, status_code: res.statusCode });
  });
  next();
});

// --- Endpoint sano: simula una consulta rapida ---
app.get('/api/orders', async (req, res) => {
  const span = trace.getActiveSpan();
  await sleep(random(20, 80));
  span?.setAttribute('orders.count', 3);
  res.json({ orders: [{ id: 1 }, { id: 2 }, { id: 3 }] });
});

// --- Endpoint lento a proposito: para ver el cuello de botella en Jaeger ---
app.get('/api/checkout', async (req, res) => {
  const span = trace.getActiveSpan();
  const tracer = trace.getTracer('apm-demo-app');

  await tracer.startActiveSpan('validateCart', async (childSpan) => {
    await sleep(random(10, 30));
    childSpan.end();
  });

  await tracer.startActiveSpan('chargePayment', async (childSpan) => {
    // Este paso es el cuello de botella intencional del ejemplo (analogo al
    // "taxApiCall" del profiling del post)
    await sleep(random(300, 600));
    childSpan.end();
  });

  span?.setAttribute('checkout.total', 149.9);
  res.json({ status: 'ok', total: 149.9 });
});

// --- Endpoint que falla a proposito: para ver errores/tasa de error ---
app.get('/api/payment-fail', async (req, res) => {
  const span = trace.getActiveSpan();
  const err = new Error('Payment gateway timeout');
  span?.recordException(err);
  res.status(500).json({ error: err.message });
});

app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

app.get('/health', (req, res) => res.json({ status: 'ok' }));

app.listen(PORT, () => {
  console.log(`apm-demo-app escuchando en puerto ${PORT}`);
});

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function random(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}
