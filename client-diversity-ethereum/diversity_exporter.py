#!/usr/bin/env python3
"""
diversity_exporter.py

Expone la distribucion de clientes de sample_distribution.json (o el
archivo que se indique con DIVERSITY_FILE) como metricas Prometheus en
http://localhost:9877/metrics, para poder scrapearlas con Prometheus y
disparar alertas segun los umbrales de client diversity (33/50/66%).

Uso:
    python3 diversity_exporter.py
    curl http://localhost:9877/metrics
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

DATA_FILE = os.environ.get("DIVERSITY_FILE", "sample_distribution.json")
PORT = int(os.environ.get("DIVERSITY_EXPORTER_PORT", "9877"))


def load_distribution() -> dict:
    with open(DATA_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def render_metrics() -> str:
    data = load_distribution()
    lines = [
        "# HELP ethereum_client_share_percent Cuota de mercado de un cliente Ethereum",
        "# TYPE ethereum_client_share_percent gauge",
    ]
    for layer, layer_type in (
        ("execution_layer", "execution"),
        ("consensus_layer", "consensus"),
    ):
        shares = data.get(layer, {})
        for client, share in shares.items():
            lines.append(
                f'ethereum_client_share_percent{{layer="{layer_type}",client="{client}"}} {share}'
            )
    return "\n".join(lines) + "\n"


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (nombre requerido por BaseHTTPRequestHandler)
        if self.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            return

        try:
            body = render_metrics().encode("utf-8")
        except (OSError, json.JSONDecodeError) as exc:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"error leyendo {DATA_FILE}: {exc}".encode("utf-8"))
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        # Silenciar el log por defecto para no ensuciar la salida del ejemplo.
        pass


def main() -> None:
    server = HTTPServer(("0.0.0.0", PORT), MetricsHandler)
    print(f"Exporter de client diversity escuchando en http://localhost:{PORT}/metrics")
    print(f"Leyendo distribucion desde: {DATA_FILE}")
    server.serve_forever()


if __name__ == "__main__":
    main()
