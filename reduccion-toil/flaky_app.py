#!/usr/bin/env python3
"""
Servicio HTTP de ejemplo que simula degradacion progresiva de salud.

Cada request a /health incrementa un contador interno. Pasado un umbral,
el servicio empieza a responder 500 (unhealthy) de forma creciente, tal
como una app real que acumula memoria/conexiones y necesita reinicio.

Al reiniciarse el proceso (por ejemplo via `docker restart`), el contador
vuelve a cero y el servicio vuelve a estar sano: por eso un restart manual
recurrente es "toil" y automatizarlo (ver watcher.sh) lo elimina.
"""
import random
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

START_TIME = time.time()
UNHEALTHY_AFTER_SECONDS = 25  # a partir de aqui empieza a degradarse
request_count = 0


class HealthHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[flaky-app] {self.address_string()} - {fmt % args}")

    def do_GET(self):
        global request_count
        if self.path == "/health":
            request_count += 1
            uptime = time.time() - START_TIME

            if uptime < UNHEALTHY_AFTER_SECONDS:
                self._respond(200, "OK\n")
                return

            # Probabilidad de fallo crece con el tiempo de uptime,
            # simulando degradacion (memory leak, conexiones colgadas, etc.)
            falla_probabilidad = min(0.9, (uptime - UNHEALTHY_AFTER_SECONDS) / 30)
            if random.random() < falla_probabilidad:
                self._respond(500, "UNHEALTHY\n")
            else:
                self._respond(200, "OK\n")
        elif self.path == "/":
            uptime = time.time() - START_TIME
            self._respond(
                200,
                f"flaky-app activo. uptime={uptime:.1f}s requests={request_count}\n",
            )
        else:
            self._respond(404, "not found\n")

    def _respond(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body.encode())


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8080), HealthHandler)
    print("[flaky-app] escuchando en :8080")
    server.serve_forever()
