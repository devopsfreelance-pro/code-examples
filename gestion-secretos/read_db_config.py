#!/usr/bin/env python3
"""
Simula una aplicacion que recupera credenciales de forma programatica
desde Vault en lugar de tenerlas hardcodeadas o en variables de entorno
sin cifrar. Usa solo la libreria estandar (urllib) para no requerir
dependencias adicionales.

Equivalente al patron usado con AWS Secrets Manager en el post del blog,
pero contra un Vault local.
"""
import json
import os
import sys
import urllib.request
import urllib.error

VAULT_ADDR = os.environ.get("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.environ.get("VAULT_TOKEN", "root-token-demo")
SECRET_PATH = "myapp/db"


def get_secret(path: str) -> dict:
    url = f"{VAULT_ADDR}/v1/secret/data/{path}"
    req = urllib.request.Request(url, headers={"X-Vault-Token": VAULT_TOKEN})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read())
    except urllib.error.URLError as exc:
        print(f"No se pudo contactar a Vault en {VAULT_ADDR}: {exc}", file=sys.stderr)
        sys.exit(1)
    return body["data"]["data"]


def main():
    creds = get_secret(SECRET_PATH)
    print("Credenciales recuperadas desde Vault (nunca hardcodeadas en el codigo):")
    print(f"  username: {creds['username']}")
    print(f"  password: {'*' * len(creds['password'])} (oculto, {len(creds['password'])} caracteres)")


if __name__ == "__main__":
    main()
