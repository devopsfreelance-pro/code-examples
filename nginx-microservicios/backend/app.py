import os
from http.server import BaseHTTPRequestHandler, HTTPServer

INSTANCE_NAME = os.environ.get("INSTANCE_NAME", "backend-desconocido")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = f'{{"instancia": "{INSTANCE_NAME}", "path": "{self.path}"}}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, format, *args):
        print(f"[{INSTANCE_NAME}] {self.address_string()} - {format % args}")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    print(f"{INSTANCE_NAME} escuchando en :8000")
    server.serve_forever()
