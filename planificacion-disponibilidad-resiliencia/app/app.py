"""
Mini backend usado en el ejemplo de alta disponibilidad.

Expone:
- GET /        -> responde con el nombre de la instancia (para ver a quien
                  esta enrutando Nginx en cada request)
- GET /health  -> healthcheck usado por Nginx para decidir si la instancia
                  sigue activa (200) o debe sacarse del pool (500)
- POST /toggle -> simula una falla: la instancia empieza a responder 500
                  en /health, como si el proceso se hubiera puesto no-sano
"""
import os
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

INSTANCE_NAME = os.environ.get("INSTANCE_NAME", socket.gethostname())

# Estado en memoria: True = sano, False = simulando falla
state = {"healthy": True}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):
        if self.path == "/health":
            if state["healthy"]:
                self._send(200, "ok\n")
            else:
                self._send(500, "unhealthy\n")
            return

        self._send(200, f"Hola desde {INSTANCE_NAME}\n")

    def do_POST(self):
        if self.path == "/toggle":
            state["healthy"] = not state["healthy"]
            estado = "sano" if state["healthy"] else "no-sano"
            self._send(200, f"{INSTANCE_NAME} ahora esta {estado}\n")
            return
        self._send(404, "not found\n")

    def log_message(self, format, *args):
        # Silenciar el log por defecto para no ensuciar la salida de docker compose
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8000), Handler)
    print(f"[{INSTANCE_NAME}] escuchando en :8000")
    server.serve_forever()
