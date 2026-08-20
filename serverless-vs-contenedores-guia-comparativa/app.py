"""
Servicio web simple que representa el modelo "contenedor": un proceso
persistente que queda arriba (warm) y atiende múltiples requests HTTP
reutilizando el mismo intérprete, sin arrancar nada nuevo por invocación.
"""
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import json


def process(text: str) -> dict:
    """Lógica de negocio compartida con serverless_sim.py."""
    return {
        "words": len(text.split()),
        "chars": len(text),
        "reversed": text[::-1],
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silenciar logs por request para no ensuciar el benchmark

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/process":
            self.send_response(404)
            self.end_headers()
            return

        qs = parse_qs(parsed.query)
        text = qs.get("text", ["hola mundo"])[0]

        result = process(text)
        body = json.dumps(result).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = 8000
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Contenedor: servidor persistente escuchando en :{port}")
    server.serve_forever()
