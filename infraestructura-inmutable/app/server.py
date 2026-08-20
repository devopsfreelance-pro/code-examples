#!/usr/bin/env python3
"""Golden image app: servidor HTTP minimo que expone su version e imagen.

La version y el color (blue/green) se hornean en la imagen via variables
de entorno definidas en el Dockerfile (ARG APP_VERSION). Esto simula el
concepto de "golden image": todo lo necesario para correr la app ya esta
dentro de la imagen, sin configuracion post-despliegue.
"""
import http.server
import json
import os
import socket


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
            return

        payload = {
            "app_version": os.environ.get("APP_VERSION", "unknown"),
            "deployment_color": os.environ.get("DEPLOYMENT_COLOR", "unknown"),
            "hostname": socket.gethostname(),
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def log_message(self, format, *args):
        # Log estructurado simple a stdout (simula envio a CloudWatch/ELK)
        print(f"{self.address_string()} - {format % args}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    server = http.server.HTTPServer(("0.0.0.0", port), Handler)
    print(f"Golden image app escuchando en :{port} (version={os.environ.get('APP_VERSION')})")
    server.serve_forever()
