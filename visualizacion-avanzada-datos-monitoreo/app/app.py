"""
Demo app minima (solo libreria estandar) que expone metricas con un
histograma real de latencia, para poder armar en Grafana:
  - un dashboard RED (Rate, Errors, Duration) con heatmap de latencia,
  - un dashboard de SLO (error budget / burn rate),
usando las mismas queries PromQL que explica el post.

Endpoints:
  GET /work     -> simula una request con latencia bimodal (rapida la
                   mayoria de las veces, lenta ~15% de las veces) y falla
                   con status 500 en ~3% de los casos.
  GET /metrics  -> metricas en formato Prometheus (texto expuesto para
                   que Prometheus las scrapee segun prometheus.yml).
"""
import random
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock

# Buckets estilo Prometheus default, en segundos.
BUCKETS = [0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]

state = {
    "success": 0,
    "error": 0,
    "duration_sum": 0.0,
    "duration_count": 0,
    # contador acumulado (no cumulativo) por bucket exacto donde cayo la latencia
    "bucket_counts": {b: 0 for b in BUCKETS},
    "bucket_counts_overflow": 0,  # latencias mayores al ultimo bucket
}
lock = Lock()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silenciar logs de acceso, ya generamos suficiente ruido

    def do_GET(self):
        if self.path == "/work":
            self._handle_work()
        elif self.path == "/metrics":
            self._handle_metrics()
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_work(self):
        start = time.time()

        # latencia bimodal: 85% requests rapidas, 15% lentas (cola pesada).
        # Esto es justo lo que un heatmap revela y un p95/p99 puede ocultar.
        if random.random() < 0.85:
            time.sleep(random.uniform(0.005, 0.08))
        else:
            time.sleep(random.uniform(0.3, 1.2))

        failed = random.random() < 0.03
        elapsed = time.time() - start

        with lock:
            state["duration_sum"] += elapsed
            state["duration_count"] += 1
            placed = False
            for b in BUCKETS:
                if elapsed <= b:
                    state["bucket_counts"][b] += 1
                    placed = True
                    break
            if not placed:
                state["bucket_counts_overflow"] += 1

            if failed:
                state["error"] += 1
            else:
                state["success"] += 1

        self.send_response(500 if failed else 200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"error\n" if failed else b"ok\n")

    def _handle_metrics(self):
        with lock:
            success = state["success"]
            error = state["error"]
            dsum = state["duration_sum"]
            dcount = state["duration_count"]
            bucket_counts = dict(state["bucket_counts"])
            overflow = state["bucket_counts_overflow"]

        lines = [
            "# HELP http_requests_total Total de requests procesados por status",
            "# TYPE http_requests_total counter",
            f'http_requests_total{{service="payment",status="200"}} {success}',
            f'http_requests_total{{service="payment",status="500"}} {error}',
            "# HELP http_request_duration_seconds Duracion de requests en segundos",
            "# TYPE http_request_duration_seconds histogram",
        ]

        # los buckets de un histograma Prometheus son CUMULATIVOS (le = "less or equal")
        cumulative = 0
        for b in BUCKETS:
            cumulative += bucket_counts[b]
            lines.append(
                f'http_request_duration_seconds_bucket{{service="payment",le="{b}"}} {cumulative}'
            )
        cumulative += overflow
        lines.append(
            f'http_request_duration_seconds_bucket{{service="payment",le="+Inf"}} {cumulative}'
        )
        lines.append(f'http_request_duration_seconds_sum{{service="payment"}} {dsum}')
        lines.append(f'http_request_duration_seconds_count{{service="payment"}} {dcount}')

        body = "\n".join(lines) + "\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8000), Handler)
    print("payment-service escuchando en :8000 (endpoints: /work, /metrics)")
    server.serve_forever()
