#!/usr/bin/env python3
"""Servidor HTTP minimo para demostrar un contenedor rootless con Podman.

Responde con informacion del proceso (PID, UID/GID) para que se pueda
verificar, desde afuera del contenedor, que el proceso corre sin
privilegios de root en el host aunque adentro del contenedor se vea
como root (UID 0).
"""
import os
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = (
            f"Hola desde un contenedor rootless con Podman\n"
            f"hostname: {socket.gethostname()}\n"
            f"PID dentro del contenedor: {os.getpid()}\n"
            f"UID dentro del contenedor: {os.getuid()}\n"
            f"GID dentro del contenedor: {os.getgid()}\n"
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, format, *args):
        # Log simple a stdout para verlo con `podman logs`
        print("%s - %s" % (self.address_string(), format % args))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Escuchando en el puerto {port} (UID={os.getuid()}, GID={os.getgid()})")
    server.serve_forever()
