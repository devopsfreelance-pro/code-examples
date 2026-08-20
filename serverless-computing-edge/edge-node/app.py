#!/usr/bin/env python3
"""
Simula una funcion serverless desplegada en un nodo edge (equivalente al
Cloudflare Worker del post: personaliza la respuesta segun la region del
usuario y devuelve metricas de la "ejecucion" de la funcion).

No usa frameworks: solo la libreria estandar, para poder correr en un
contenedor python:3.12-slim sin instalar nada.
"""
import http.server
import json
import os
import socket
import time

REGION = os.environ.get("REGION", "unknown")

REGION_MESSAGES = {
    "us": "Hello from the edge (US)!",
    "eu": "Hello from the edge (EU)!",
    "sa": "¡Hola desde el edge (Sudamerica)!",
}

# Latencias de red "simuladas" solo para ilustrar el concepto del post
# (procesar cerca del usuario reduce la latencia percibida). No son mediciones
# reales de red.
REGION_SIMULATED_NETWORK_LATENCY_MS = {
    "us": 12,
    "eu": 18,
    "sa": 9,
}


class EdgeFunctionHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        start = time.perf_counter()

        # Pequeña demora artificial para representar el tiempo de ejecucion
        # de la funcion (equivalente al "handleRequest" del ejemplo JS).
        time.sleep(0.01)

        body = {
            "region": REGION,
            "edge_node_hostname": socket.gethostname(),
            "message": REGION_MESSAGES.get(REGION, "Hello from the edge!"),
            "simulated_network_latency_ms": REGION_SIMULATED_NETWORK_LATENCY_MS.get(
                REGION, 50
            ),
            "function_exec_time_ms": round((time.perf_counter() - start) * 1000, 2),
        }
        payload = json.dumps(body, ensure_ascii=False, indent=2).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        # Silenciamos el logging por defecto para mantener la salida limpia.
        pass


if __name__ == "__main__":
    server = http.server.ThreadingHTTPServer(("0.0.0.0", 8000), EdgeFunctionHandler)
    print(f"Edge function [{REGION}] escuchando en :8000")
    server.serve_forever()
