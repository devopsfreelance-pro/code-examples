"""
payment-service de juguete usado en el experimento de Chaos Engineering.

Servidor HTTP minimo (solo libreria estandar) que expone GET /health.
Se ejecuta como 3 instancias independientes via docker-compose, igual
que el "payment-service" del ejemplo del post.
"""
import json
import os
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer

INSTANCE_ID = socket.gethostname()


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body = json.dumps(
                {"status": "ok", "service": "payment-service", "instance": INSTANCE_ID}
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silenciar el logging por request para no ensuciar la salida
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"payment-service instance {INSTANCE_ID} escuchando en :{port}")
    server.serve_forever()
