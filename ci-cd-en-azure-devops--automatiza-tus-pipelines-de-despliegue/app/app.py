"""
Aplicación mínima usada como ejemplo de "carga útil" del pipeline de CI/CD.

Solo usa la librería estándar de Python (sin dependencias externas) para que
el ejemplo se pueda ejecutar y testear en segundos, tal como haría el stage
"Build and Test" del pipeline de Azure DevOps del post.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os


def build_health_payload():
    """Lógica de negocio separada del handler HTTP para poder testearla
    directamente, sin levantar un servidor real."""
    return {
        "status": "ok",
        "service": "myapp",
        "environment": os.environ.get("APP_ENVIRONMENT", "development"),
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            payload = build_health_payload()
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silenciar el logging por defecto para no ensuciar la salida del pipeline
        pass


def run(port=8080):
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"myapp escuchando en el puerto {port}")
    server.serve_forever()


if __name__ == "__main__":
    run(int(os.environ.get("PORT", "8080")))
