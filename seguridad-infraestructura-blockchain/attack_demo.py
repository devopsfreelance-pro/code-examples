#!/usr/bin/env python3
"""
Simula, contra el mock de RPC, dos de los abusos que el post menciona
cuando un puerto RPC (8545) queda expuesto:

1. Fingerprinting del cliente (web3_clientVersion) sin ninguna
   autenticacion: el primer paso de cualquier scanner automatico.
2. Enumeracion de cuentas "desbloqueadas" (eth_accounts): si un nodo
   mal configurado responde algo distinto de una lista vacia, es
   candidato a vaciado de fondos.
3. Una consulta eth_getLogs pesada, representativa del vector de
   denegacion de servicio contra RPCs publicos.

Uso:
    python3 attack_demo.py http://localhost:8545
"""
import json
import sys
import time
import urllib.request


def rpc_call(url, method, params=None):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def main():
    if len(sys.argv) != 2:
        print("Uso: python3 attack_demo.py <url-del-rpc>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]

    print(f"[1] Fingerprinting sin autenticacion contra {url}")
    try:
        version = rpc_call(url, "web3_clientVersion")
        print("    Respuesta:", version["result"])
    except Exception as exc:
        print("    No se pudo conectar (esto es lo esperado si el RPC esta restringido):", exc)
        sys.exit(0)

    print("[2] Intentando enumerar cuentas (eth_accounts)")
    accounts = rpc_call(url, "eth_accounts")
    print("    Cuentas expuestas:", accounts["result"])
    if accounts["result"]:
        print("    RIESGO: el nodo respondio con cuentas. En un nodo real esto habilita firmar transacciones.")

    print("[3] Consulta pesada eth_getLogs (vector de DoS)")
    start = time.time()
    logs = rpc_call(url, "eth_getLogs", [{"fromBlock": "0x0", "toBlock": "latest"}])
    total = time.time() - start
    print(f"    Tiempo total de la llamada: {total:.3f}s (server reporto {logs['result']['elapsed_seconds']}s de trabajo)")
    print("    En un nodo real, repetir esto en paralelo desde muchos scanners degrada el servicio.")


if __name__ == "__main__":
    main()
