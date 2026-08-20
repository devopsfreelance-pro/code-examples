#!/usr/bin/env python3
"""
Servicio demo instrumentado con prometheus_client, igual al ejemplo del post:
- Histogram http_request_duration_seconds (latencia)
- Counter http_requests_total{method,endpoint,status} (para el burn rate)

Endpoints:
  GET  /api/search?q=...      -> simula la busqueda de productos del post
  POST /admin/error-rate?p=X  -> ajusta la tasa de error 5xx en caliente (0.0 a 1.0)
  GET  /metrics                -> expuesto en el puerto 9100 (servidor separado)
"""
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from prometheus_client import Counter, Histogram, start_http_server

request_latency = Histogram(
    "http_request_duration_seconds",
    "Latencia de solicitudes HTTP",
    ["method", "endpoint"],
)

requests_total = Counter(
    "http_requests_total",
    "Total de solicitudes HTTP por status",
    ["method", "endpoint", "status"],
)

# Tasa de error 5xx ajustable en runtime (arranca baja, dentro del SLO 99.9%)
state = {"error_rate": 0.0005}
state_lock = threading.Lock()


def search_products(query):
    """Simula la logica de busqueda del post: latencia variable + errores."""
    method, endpoint = "GET", "/api/search"
    start = time.perf_counter()
    with state_lock:
        error_rate = state["error_rate"]

    # Latencia realista: mayoria rapida, cola larga ocasional
    time.sleep(random.uniform(0.01, 0.08) if random.random() > 0.05 else random.uniform(0.1, 0.3))

    is_error = random.random() < error_rate
    status = "500" if is_error else "200"

    elapsed = time.perf_counter() - start
    request_latency.labels(method=method, endpoint=endpoint).observe(elapsed)
    requests_total.labels(method=method, endpoint=endpoint, status=status).inc()

    if is_error:
        return 500, {"error": "internal error"}
    return 200, {"query": query, "results": ["sku-1", "sku-2", "sku-3"]}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silenciar logs de acceso, ruido innecesario en la demo

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/search":
            qs = parse_qs(parsed.query)
            query = qs.get("q", [""])[0]
            status, body = search_products(query)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(str(body).encode())
        elif parsed.path == "/healthz":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/admin/error-rate":
            qs = parse_qs(parsed.query)
            try:
                p = float(qs.get("p", ["0.0005"])[0])
            except ValueError:
                p = 0.0005
            p = max(0.0, min(1.0, p))
            with state_lock:
                state["error_rate"] = p
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(f'{{"error_rate": {p}}}'.encode())
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    # Servidor de metricas Prometheus en :9100 (/metrics)
    start_http_server(9100)
    print("Metrics en http://0.0.0.0:9100/metrics")
    print("API en http://0.0.0.0:8080/api/search?q=zapatillas")
    server = ThreadingHTTPServer(("0.0.0.0", 8080), Handler)
    server.serve_forever()
