"""
Mini servidor HTTP que expone informacion del proceso y del cgroup
en el que esta corriendo el contenedor: PID, hostname, y los limites
de CPU/memoria que el runtime (Docker o Podman) le asigno via cgroups.

Sirve para comprobar en la practica lo que el post explica en teoria:
un contenedor NO es una VM, es un proceso Linux aislado con namespaces
y limitado por cgroups, corriendo sobre el mismo kernel del host.
"""

import http.server
import json
import os
import socket


def read_first_existing(paths):
    for path in paths:
        try:
            with open(path) as f:
                return path, f.read().strip()
        except FileNotFoundError:
            continue
    return None, None


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        cpu_path, cpu_quota = read_first_existing([
            "/sys/fs/cgroup/cpu.max",              # cgroups v2
            "/sys/fs/cgroup/cpu/cpu.cfs_quota_us",  # cgroups v1
        ])
        mem_path, mem_limit = read_first_existing([
            "/sys/fs/cgroup/memory.max",            # cgroups v2
            "/sys/fs/cgroup/memory/memory.limit_in_bytes",  # cgroups v1
        ])

        payload = {
            "hostname": socket.gethostname(),
            "pid_dentro_del_contenedor": os.getpid(),
            "cgroup_cpu_limit_path": cpu_path,
            "cgroup_cpu_limit_value": cpu_quota,
            "cgroup_mem_limit_path": mem_path,
            "cgroup_mem_limit_value": mem_limit,
        }

        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # silenciar logs de acceso, no aportan al demo


if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", 8080), Handler)
    print("Escuchando en :8080")
    server.serve_forever()
