"""
Mini API que ilustra tres controles de secure coding exigidos por PCI DSS
(ver post: PCI DSS - Guia Completa para Aplicaciones Seguras 2026):

- Requisito 2 / 6.2: sin credenciales hardcodeadas. La password de la DB se
  lee de un secret file montado por Docker (DB_PASSWORD_FILE), nunca del
  codigo fuente ni de una variable de entorno en texto plano.
- Requisito 3: solo se maneja un token de tarjeta y los ultimos 4 digitos.
  El PAN completo jamas se almacena ni se expone.
- Requisito 6.2 (OWASP Top 10 - SQL Injection): todas las consultas usan
  sentencias parametrizadas (prepared statements) en lugar de concatenar
  el input del usuario en el SQL.
- Requisito 10: cada acceso a datos del titular de la tarjeta se loguea.
"""
import logging
import os
import re
import sys

import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s level=%(levelname)s event=%(message)s",
)
log = logging.getLogger("pci-demo")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def read_secret(env_var_file: str, env_var_plain: str) -> str:
    """Lee un secreto desde un secret file (preferido) o, como fallback
    solo para desarrollo local sin Docker secrets, desde una env var."""
    path = os.environ.get(env_var_file)
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read().strip()
    return os.environ.get(env_var_plain, "")


def get_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=read_secret("DB_PASSWORD_FILE", "DB_PASSWORD"),
    )


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/token-lookup")
def token_lookup():
    """Devuelve solo el token y last4 asociados a un email. Nunca el PAN."""
    email = request.args.get("email", "")

    # Requisito 6.2: validacion estricta de entrada (lista de permitidos).
    if not EMAIL_RE.match(email):
        log.warning("invalid_input email_lookup rejected")
        return jsonify(error="email invalido"), 400

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Consulta PARAMETRIZADA: %s + tupla de parametros.
            # psycopg2 escapa el valor, imposibilitando SQL injection.
            cur.execute(
                "SELECT card_token, last4 FROM card_tokens "
                "WHERE customer_email = %s",
                (email,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    # Requisito 10: log de todo acceso a datos del titular de la tarjeta,
    # sin loguear el dato sensible en si.
    log.info(f"cardholder_data_access email={email} found={row is not None}")

    if row is None:
        return jsonify(error="no encontrado"), 404
    return jsonify(card_token=row[0], last4=row[1])


@app.get("/token-lookup-vulnerable-example")
def token_lookup_vulnerable_example():
    """
    NO USAR EN PRODUCCION. Se deja documentado a proposito para el post:
    esta es la version INSEGURA (concatenacion de strings) que el
    Requisito 6.2 de PCI DSS prohibe, y que un SAST deberia bloquear
    antes de llegar a produccion. No se ejecuta ninguna query real aqui.
    """
    email = request.args.get("email", "")
    unsafe_query = "SELECT card_token FROM card_tokens WHERE customer_email = '" + email + "'"
    return jsonify(
        warning="ejemplo educativo, no ejecutado",
        unsafe_query=unsafe_query,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
