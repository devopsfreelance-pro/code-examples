#!/usr/bin/env python3
"""
Servicio HTTP minimo instrumentado con los SLI que describe el post
"SLI SLO SLA: Guia Practica para Medir Calidad de Servicio"
(https://www.devopsfreelance.pro/blog/posts/slis-slos-slas/).

Expone:
  GET /work                    -> simula una solicitud real (latencia variable, algunos errores)
  GET /admin/degrade?on=1      -> activa modo degradado (sube el 5xx, para ver caer el SLI)
  GET /admin/degrade?on=0      -> vuelve a modo normal
  :9100/metrics                -> metricas Prometheus

Metricas (las mismas que usa el ejemplo de codigo del post):
  http_request_duration_seconds  Histogram por metodo/endpoint
  http_requests_total            Counter por metodo/endpoint/status
"""
import http.server
import os
import random
import socketserver
import threading
import time

from prometheus_client import Counter, Histogram, start_http_server

APP_PORT = int(os.environ.get("APP_PORT", "8080"))
METRICS_PORT = int(os.environ.get("METRICS_PORT", "9100"))

request_latency = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.5, 5.0],
)
requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

DEGRADED = threading.Event()


def record_request_metrics(method, endpoint, status, duration):
    request_latency.labels(method=method, endpoint=endpoint).observe(duration)
    requests_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silenciar el log de acceso por defecto de BaseHTTPRequestHandler

    def do_GET(self):
        if self.path.startswith("/admin/degrade"):
            self._handle_degrade()
            return
        if self.path.startswith("/work"):
            self._handle_work()
            return
        self.send_response(404)
        self.end_headers()

    def _handle_degrade(self):
        on = "on=1" in self.path
        if on:
            DEGRADED.set()
        else:
            DEGRADED.clear()
        body = f"modo degradado: {'ON' if DEGRADED.is_set() else 'OFF'}\n".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body)

    def _handle_work(self):
        start = time.time()

        # Latencia realista: la mayoria rapido, con una cola larga ocasional
        base_latency = random.uniform(0.02, 0.15)
        if random.random() < 0.05:
            base_latency += random.uniform(0.3, 1.5)
        time.sleep(base_latency)

        error_rate_5xx = 0.25 if DEGRADED.is_set() else 0.003
        error_rate_4xx = 0.02  # no cuenta contra el SLI de confiabilidad (segun el post)

        roll = random.random()
        if roll < error_rate_5xx:
            status = 500
        elif roll < error_rate_5xx + error_rate_4xx:
            status = 404
        else:
            status = 200

        duration = time.time() - start
        record_request_metrics("GET", "/work", status, duration)

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(f'{{"status": {status}}}'.encode())


def main():
    start_http_server(METRICS_PORT)
    print(f"Metricas Prometheus en :{METRICS_PORT}/metrics")
    with socketserver.ThreadingTCPServer(("0.0.0.0", APP_PORT), Handler) as httpd:
        print(f"App sirviendo /work en :{APP_PORT}")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
