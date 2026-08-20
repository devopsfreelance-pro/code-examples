"""
Mini app usada para demostrar el ciclo de vida DevOps: Code -> Build -> Test -> Deploy.

Servidor HTTP minimo (solo libreria estandar, sin dependencias externas) con dos
endpoints:
  - GET /health  -> estado del servicio (para probes de Kubernetes/Docker)
  - GET /         -> mensaje de bienvenida con la version de la app

La logica de negocio esta separada en funciones puras (health_payload, root_payload)
para poder testearlas sin levantar un servidor real, tal como lo haria un pipeline
de CI real (fase "Test" del ciclo DevOps).
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

APP_VERSION = "1.0.0"


def health_payload() -> dict:
    """Payload devuelto por /health. Logica pura, facil de testear."""
    return {"status": "ok", "version": APP_VERSION}


def root_payload() -> dict:
    """Payload devuelto por /. Logica pura, facil de testear."""
    return {"message": "Hola DevOps", "version": APP_VERSION}


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 (nombre requerido por BaseHTTPRequestHandler)
        if self.path == "/health":
            self._send_json(health_payload())
        elif self.path == "/":
            self._send_json(root_payload())
        else:
            self._send_json({"error": "not found"}, status=404)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        # Silencia el logging por defecto para no ensuciar la salida de docker compose
        return


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Escuchando en http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
