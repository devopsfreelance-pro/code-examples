#!/usr/bin/env python3
"""
Demo de Authorization Code Flow con PKCE contra un Keycloak local.

Ilustra el flujo moderno recomendado para SPA y apps nativas descrito en el
post: genera code_verifier/code_challenge, abre el navegador para que el
usuario se autentique en Keycloak, recibe el authorization code en un
callback local y lo intercambia por tokens (access_token e id_token).

Solo usa la librería estándar de Python (sin dependencias externas).
"""
import base64
import hashlib
import http.server
import json
import secrets
import threading
import urllib.parse
import urllib.request
import webbrowser

KEYCLOAK_BASE = "http://localhost:8080/realms/demo/protocol/openid-connect"
CLIENT_ID = "demo-app"
REDIRECT_URI = "http://localhost:8000/callback"
CALLBACK_PORT = 8000

_result = {}
_done = threading.Event()


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # silenciar logs por defecto del servidor HTTP

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        params = urllib.parse.parse_qs(parsed.query)
        _result["code"] = params.get("code", [None])[0]
        _result["state"] = params.get("state", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"<h1>Autenticacion completa</h1><p>Podes cerrar esta pestana y volver a la terminal.</p>"
        )
        _done.set()


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def generate_pkce_pair():
    code_verifier = b64url(secrets.token_bytes(32))
    code_challenge = b64url(hashlib.sha256(code_verifier.encode("utf-8")).digest())
    return code_verifier, code_challenge


def decode_jwt_payload(token: str) -> dict:
    """Decodifica (sin verificar firma) el payload de un JWT para inspeccion.

    En produccion la validacion de firma/expiracion es obligatoria: usar
    las claves publicas del endpoint JWKS del servidor de autorizacion.
    """
    payload_b64 = token.split(".")[1]
    padding = "=" * (-len(payload_b64) % 4)
    payload_json = base64.urlsafe_b64decode(payload_b64 + padding)
    return json.loads(payload_json)


def main():
    code_verifier, code_challenge = generate_pkce_pair()
    state = secrets.token_urlsafe(16)
    nonce = secrets.token_urlsafe(16)

    auth_params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "openid profile email",
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    authorization_url = f"{KEYCLOAK_BASE}/auth?{urllib.parse.urlencode(auth_params)}"

    server = http.server.HTTPServer(("localhost", CALLBACK_PORT), CallbackHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    print("Abriendo el navegador para autenticarse en Keycloak...")
    print(f"Si no se abre solo, visitá:\n{authorization_url}\n")
    print("Usuario de prueba: demo / demo123\n")
    webbrowser.open(authorization_url)

    print("Esperando el callback en http://localhost:8000/callback ...")
    _done.wait(timeout=180)
    server.shutdown()

    if not _result.get("code"):
        print("No se recibió ningún code. Abortando.")
        return

    if _result.get("state") != state:
        print("El parámetro 'state' no coincide, posible CSRF. Abortando.")
        return

    print(f"Authorization code recibido: {_result['code'][:12]}...\n")

    token_data = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "code": _result["code"],
            "redirect_uri": REDIRECT_URI,
            "code_verifier": code_verifier,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        f"{KEYCLOAK_BASE}/token",
        data=token_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        tokens = json.loads(resp.read().decode("utf-8"))

    print("Tokens recibidos del servidor de autorización:")
    print(f"  access_token (primeros 24 chars): {tokens['access_token'][:24]}...")
    print(f"  id_token (primeros 24 chars):     {tokens['id_token'][:24]}...")
    print(f"  expires_in: {tokens['expires_in']} segundos\n")

    id_claims = decode_jwt_payload(tokens["id_token"])
    print("Claims del ID Token (identidad del usuario, sin verificar firma aquí):")
    for key in ("sub", "email", "preferred_username", "name", "iat", "exp"):
        if key in id_claims:
            print(f"  {key}: {id_claims[key]}")

    if id_claims.get("nonce") != nonce:
        print("\nADVERTENCIA: el nonce del ID Token no coincide con el enviado.")


if __name__ == "__main__":
    main()
