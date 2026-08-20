#!/usr/bin/env python3
"""
Mock de un nodo Ethereum (cliente de ejecucion tipo geth o cliente de
consenso tipo lighthouse) para poder probar scripts de automatizacion
sin correr un nodo real.

Variables de entorno:
  MODE          "execution" o "consensus" (default: execution)
  PEERS         cantidad de peers a reportar (default: 8)
  SYNCING       "true" o "false" (default: false)
  HEALTH_CODE   codigo HTTP para /eth/v1/node/health (default: 200)
  PORT          puerto a escuchar (default: 8545 execution / 5052 consensus)
"""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

MODE = os.environ.get("MODE", "execution")
PEERS = int(os.environ.get("PEERS", "8"))
SYNCING = os.environ.get("SYNCING", "false").lower() == "true"
HEALTH_CODE = int(os.environ.get("HEALTH_CODE", "200"))
DEFAULT_PORT = 8545 if MODE == "execution" else 5052
PORT = int(os.environ.get("PORT", str(DEFAULT_PORT)))


class NodeHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[{MODE}] {self.address_string()} - {fmt % args}")

    def _json(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        # JSON-RPC del cliente de ejecucion (eth_syncing, net_peerCount)
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            req = json.loads(raw)
        except json.JSONDecodeError:
            req = {}
        method = req.get("method", "")
        rpc_id = req.get("id", 1)

        if method == "eth_syncing":
            result = False if not SYNCING else {"currentBlock": "0x1", "highestBlock": "0x64"}
            self._json(200, {"jsonrpc": "2.0", "id": rpc_id, "result": result})
        elif method == "net_peerCount":
            self._json(200, {"jsonrpc": "2.0", "id": rpc_id, "result": hex(PEERS)})
        else:
            self._json(200, {"jsonrpc": "2.0", "id": rpc_id, "result": None})

    def do_GET(self):
        if self.path == "/eth/v1/node/health":
            self.send_response(HEALTH_CODE)
            self.end_headers()
        elif self.path == "/eth/v1/node/syncing":
            self._json(200, {"data": {"is_syncing": SYNCING}})
        else:
            self._json(404, {"error": "not found"})


if __name__ == "__main__":
    print(f"Mock {MODE} node escuchando en 0.0.0.0:{PORT} "
          f"(peers={PEERS}, syncing={SYNCING}, health_code={HEALTH_CODE})")
    HTTPServer(("0.0.0.0", PORT), NodeHandler).serve_forever()
