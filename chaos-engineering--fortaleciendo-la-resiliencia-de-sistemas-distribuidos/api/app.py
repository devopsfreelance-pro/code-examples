"""Servicio HTTP minimo que simula el health-check de un microservicio de pagos.

No tiene dependencias externas: usa solo la libreria estandar de Python
para que el ejemplo corra con la imagen oficial python:3.11-slim sin
necesidad de instalar nada.
"""
import http.server
import json


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body = json.dumps({"status": "ok", "service": "payment-service"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):  # silenciar logs de acceso
        pass


if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", 5000), Handler)
    print("payment-service escuchando en :5000")
    server.serve_forever()
