"""
Demo app minima que expone metricas en formato Prometheus.

Endpoints:
  GET /work     -> simula trabajo con latencia variable, a veces falla
  GET /metrics  -> metricas en formato Prometheus (scrapeadas por prometheus.yml)
"""
import random
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock

request_count = {"success": 0, "error": 0}
duration_sum = 0.0
duration_count = 0
lock = Lock()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silenciar logs de acceso

    def do_GET(self):
        if self.path == "/work":
            self._handle_work()
        elif self.path == "/metrics":
            self._handle_metrics()
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_work(self):
        global duration_sum, duration_count
        start = time.time()
        # simula latencia variable
        time.sleep(random.uniform(0.01, 0.3))
        failed = random.random() < 0.05
        elapsed = time.time() - start

        with lock:
            duration_sum += elapsed
            duration_count += 1
            if failed:
                request_count["error"] += 1
            else:
                request_count["success"] += 1

        self.send_response(500 if failed else 200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"error\n" if failed else b"ok\n")

    def _handle_metrics(self):
        with lock:
            success = request_count["success"]
            error = request_count["error"]
            dsum = duration_sum
            dcount = duration_count

        body = (
            "# HELP app_requests_total Total de requests procesados por status\n"
            "# TYPE app_requests_total counter\n"
            f'app_requests_total{{status="success"}} {success}\n'
            f'app_requests_total{{status="error"}} {error}\n'
            "# HELP app_request_duration_seconds_sum Suma de duracion de requests\n"
            "# TYPE app_request_duration_seconds_sum counter\n"
            f"app_request_duration_seconds_sum {dsum}\n"
            "# HELP app_request_duration_seconds_count Cantidad de requests medidos\n"
            "# TYPE app_request_duration_seconds_count counter\n"
            f"app_request_duration_seconds_count {dcount}\n"
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8000), Handler)
    print("demo_app escuchando en :8000 (endpoints: /work, /metrics)")
    server.serve_forever()
