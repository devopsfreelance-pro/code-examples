#!/usr/bin/env python3
"""Servidor HTTP minimo usado como 'aplicacion' del servicio de ejemplo.

Se gestiona con systemd (webapp.service). Responde OK en / y expone un
endpoint /crash que termina el proceso con codigo de error, para poder
demostrar la politica Restart=on-failure de systemd.
"""
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Los logs van a stdout -> journald los captura via StandardOutput=journal
        sys.stdout.write("%s - %s\n" % (self.address_string(), fmt % args))

    def do_GET(self):
        if self.path == "/crash":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Forzando caida del proceso...\n")
            sys.exit(1)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - webapp gestionada por systemd\n")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), Handler)
    print("webapp escuchando en :8080 (PID gestionado por systemd)")
    server.serve_forever()
