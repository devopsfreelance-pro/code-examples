#!/usr/bin/env python3
"""
Demo app usada en el ejemplo de gestion de incidentes.

Expone dos servidores HTTP (solo libreria estandar, sin dependencias):

  - Puerto 8000: endpoint /metrics en formato Prometheus con una metrica
    gauge (demo_api_error_rate) que simula la tasa de error de una API.
    Tambien expone /trigger y /resolve para simular el inicio y la
    resolucion de un incidente.

  - Puerto 9000: endpoint /webhook que recibe las notificaciones de
    Alertmanager y las imprime por stdout simulando la notificacion al
    ingeniero on-call (equivalente al escalamiento de PagerDuty descrito
    en el post).
"""
import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

state_lock = threading.Lock()
state = {"error_mode": False}


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"{ts} {msg}", flush=True)


class MetricsHandler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: str, content_type: str = "text/plain") -> None:
        payload = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/metrics":
            with state_lock:
                error_rate = 0.80 if state["error_mode"] else 0.01
            body = (
                "# HELP demo_api_error_rate Tasa de error simulada de la API\n"
                "# TYPE demo_api_error_rate gauge\n"
                f"demo_api_error_rate {error_rate}\n"
            )
            self._send(200, body, "text/plain; version=0.0.4")
        else:
            self._send(404, "not found\n")

    def do_POST(self):
        if self.path == "/trigger":
            with state_lock:
                state["error_mode"] = True
            log("INCIDENTE SIMULADO: error_mode=ON (demo_api_error_rate=0.80)")
            self._send(200, "incident triggered\n")
        elif self.path == "/resolve":
            with state_lock:
                state["error_mode"] = False
            log("INCIDENTE RESUELTO: error_mode=OFF (demo_api_error_rate=0.01)")
            self._send(200, "incident resolved\n")
        else:
            self._send(404, "not found\n")

    def log_message(self, fmt, *args):
        # Silenciar el log por defecto de BaseHTTPRequestHandler,
        # usamos nuestro propio log() para los eventos relevantes.
        pass


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            payload = {}

        for alert in payload.get("alerts", []):
            status = alert.get("status", "unknown")
            labels = alert.get("labels", {})
            annotations = alert.get("annotations", {})
            alertname = labels.get("alertname", "desconocido")
            severity = labels.get("severity", "desconocida")
            summary = annotations.get("summary", "sin resumen")
            runbook = annotations.get("runbook", "sin runbook")

            if status == "firing":
                log(
                    f"[ESCALAMIENTO] Notificando a ingeniero on-call primario -> "
                    f"alerta={alertname} severity={severity} resumen='{summary}' "
                    f"runbook={runbook}"
                )
            else:
                log(f"[RESUELTO] alerta={alertname} status={status}")

        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, fmt, *args):
        pass


def serve(handler_cls, port: int) -> None:
    server = ThreadingHTTPServer(("0.0.0.0", port), handler_cls)
    server.serve_forever()


if __name__ == "__main__":
    metrics_thread = threading.Thread(target=serve, args=(MetricsHandler, 8000), daemon=True)
    webhook_thread = threading.Thread(target=serve, args=(WebhookHandler, 9000), daemon=True)
    metrics_thread.start()
    webhook_thread.start()
    log("demo-app arriba: /metrics en :8000, /webhook en :9000")
    metrics_thread.join()
    webhook_thread.join()
