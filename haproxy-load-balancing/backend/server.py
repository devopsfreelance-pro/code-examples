#!/usr/bin/env python3
"""Servidor HTTP minimo que identifica en cada respuesta que backend respondio.

Se usa como servidor de aplicacion "backend" detras de HAProxy. Expone:
  GET /        -> identifica el backend y cuenta peticiones servidas
  GET /health  -> 200 OK normal, o 503 si se activo modo "caido" via /toggle-health
  GET /toggle-health -> alterna el backend entre sano y caido (para probar failover)
  GET /slow    -> responde con latencia artificial (para probar leastconn)
"""
import os
import time
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BACKEND_NAME = os.environ.get("BACKEND_NAME", "backend-desconocido")
PORT = int(os.environ.get("PORT", "8080"))

state = {"healthy": True, "requests": 0}


class Handler(BaseHTTPRequestHandler):
    def _json(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            if state["healthy"]:
                self._json(200, {"status": "ok", "backend": BACKEND_NAME})
            else:
                self._json(503, {"status": "down", "backend": BACKEND_NAME})
            return

        if self.path == "/toggle-health":
            state["healthy"] = not state["healthy"]
            self._json(200, {"backend": BACKEND_NAME, "healthy": state["healthy"]})
            return

        if self.path == "/slow":
            time.sleep(1.5)
            state["requests"] += 1
            self._json(200, {"backend": BACKEND_NAME, "requests": state["requests"], "slow": True})
            return

        state["requests"] += 1
        self._json(200, {"backend": BACKEND_NAME, "requests": state["requests"]})

    def log_message(self, format, *args):
        # silenciar logs por request para no ensuciar la salida de docker compose
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"{BACKEND_NAME} escuchando en puerto {PORT}")
    server.serve_forever()
