#!/usr/bin/env python3
"""
Mock de un endpoint JSON-RPC estilo Ethereum (subset minimo), pensado
solo para demostrar el riesgo de exponer el puerto RPC (8545) tal como
se describe en el post "Seguridad en infraestructura blockchain".

No es un cliente real (no usa web3, no firma nada). Simula:
- web3_clientVersion: identificacion trivial del cliente (fingerprinting)
- eth_accounts: lista de cuentas "desbloqueadas" (peligroso si esta habilitado)
- eth_getLogs: consulta pesada usada para tirar el nodo con requests caras
"""
import http.server
import json
import socketserver
import sys
import time

# Cuentas de juguete: jamas hay llaves reales en este ejemplo.
FAKE_ACCOUNTS = ["0xDEMO0000000000000000000000000000000001"]


class RPCHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("[mock-rpc] %s - %s\n" % (self.address_string(), fmt % args))

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            req = json.loads(raw)
        except json.JSONDecodeError:
            self._send_json({"jsonrpc": "2.0", "error": {"code": -32700, "message": "parse error"}}, 400)
            return

        method = req.get("method")
        req_id = req.get("id", 1)

        if method == "web3_clientVersion":
            result = "MockGeth/v0.0.0-demo/linux-amd64/python3"
        elif method == "eth_accounts":
            # En un nodo real, esto solo deberia responder algo si el
            # RPC quedo mal configurado con cuentas desbloqueadas.
            result = FAKE_ACCOUNTS
        elif method == "eth_getLogs":
            # Simula el costo de una consulta de rango amplio sin filtros:
            # esta es la clase de llamada que un atacante usa para
            # saturar CPU/IO de un RPC publico.
            start = time.time()
            _ = [i * i for i in range(2_000_000)]
            elapsed = time.time() - start
            result = {"note": "consulta pesada simulada", "elapsed_seconds": round(elapsed, 3), "logs": []}
        else:
            self._send_json(
                {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "method not found"}}
            )
            return

        self._send_json({"jsonrpc": "2.0", "id": req_id, "result": result})

    def do_GET(self):
        self._send_json({"status": "ok", "hint": "usar POST JSON-RPC, ver README"})


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8545
    with socketserver.TCPServer((host, port), RPCHandler) as httpd:
        print(f"[mock-rpc] escuchando en {host}:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
