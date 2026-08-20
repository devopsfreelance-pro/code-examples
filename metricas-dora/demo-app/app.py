#!/usr/bin/env python3
"""
Servicio de demo minimo (solo libreria estandar) que expone metricas
en formato Prometheus para ilustrar como se detecta una degradacion
de servicio y se dispara una alerta -- la base para poder medir MTTR.

Endpoints:
    GET  /work           -> simula una request de negocio (200 o 500)
    GET  /toggle-errors   -> activa/desactiva una tasa de error alta
    GET  /metrics         -> expone contadores en formato Prometheus
    GET  /health           -> health check simple
"""
import random
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOCK = threading.Lock()
COUNTERS = {"200": 0, "500": 0}
ERRORS_ENABLED = {"value": False}

NORMAL_ERROR_RATE = 0.02   # 2%, comportamiento sano
INCIDENT_ERROR_RATE = 0.35  # 35%, simula un incidente en produccion


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silencia el logging por request para no ensuciar la salida

    def _send(self, status: int, body: bytes, content_type: str = "text/plain"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/work":
            rate = INCIDENT_ERROR_RATE if ERRORS_ENABLED["value"] else NORMAL_ERROR_RATE
            status = "500" if random.random() < rate else "200"
            with LOCK:
                COUNTERS[status] += 1
            self._send(500 if status == "500" else 200, f"status={status}\n".encode())

        elif self.path == "/toggle-errors":
            with LOCK:
                ERRORS_ENABLED["value"] = not ERRORS_ENABLED["value"]
                estado = "INCIDENTE (35% error)" if ERRORS_ENABLED["value"] else "NORMAL (2% error)"
            self._send(200, f"modo={estado}\n".encode())

        elif self.path == "/metrics":
            with LOCK:
                total_200 = COUNTERS["200"]
                total_500 = COUNTERS["500"]
            body = (
                "# HELP http_requests_total Total de requests procesadas por status\n"
                "# TYPE http_requests_total counter\n"
                f'http_requests_total{{status="200"}} {total_200}\n'
                f'http_requests_total{{status="500"}} {total_500}\n'
            )
            self._send(200, body.encode())

        elif self.path == "/health":
            self._send(200, b"ok\n")

        else:
            self._send(404, b"not found\n")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8080), Handler)
    print("demo-app escuchando en :8080")
    server.serve_forever()
