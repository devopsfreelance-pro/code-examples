"""
Receptor de webhooks minimo para simular 3 canales de notificacion
(critical / high / default) tal como los describe el post: cada nivel
de severidad va a una ruta distinta con su propia urgencia.

No usa dependencias externas: solo http.server de la stdlib.
"""
import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CHANNELS = {
    9091: "CRITICAL -> llamada/SMS (interrumpe ya)",
    9092: "HIGH     -> Slack con mencion",
    9093: "DEFAULT  -> canal de equipo / reporte periodico",
}


class WebhookHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # silenciar el log default de http.server, usamos el nuestro
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {}

        channel = CHANNELS.get(self.server.server_port, "desconocido")
        alerts = payload.get("alerts", [])
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")

        print(f"\n[{ts}] === Notificacion recibida en canal {self.server.server_port} ===")
        print(f"Canal: {channel}")
        print(f"Alertas agrupadas en este envio: {len(alerts)}")
        for a in alerts:
            labels = a.get("labels", {})
            status = a.get("status", "?")
            print(
                f"  - alertname={labels.get('alertname')} "
                f"service={labels.get('service')} "
                f"severity={labels.get('severity')} "
                f"status={status}"
            )
        print("=" * 60, flush=True)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")


def serve(port: int):
    server = ThreadingHTTPServer(("0.0.0.0", port), WebhookHandler)
    server.serve_forever()


if __name__ == "__main__":
    print("Receptor de alertas escuchando en:")
    for port, desc in CHANNELS.items():
        print(f"  puerto {port}: {desc}")

    threads = [
        threading.Thread(target=serve, args=(port,), daemon=True)
        for port in CHANNELS
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
