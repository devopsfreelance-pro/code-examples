"""
Mini payment-service usado como ejemplo del post "Integracion continua en
microservicios". Expone una API HTTP minima con:

  GET  /health              -> chequeo de salud (usado por el pipeline)
  POST /pay                 -> procesa un pago (usa Postgres real, no un mock)

La logica de negocio (calculate_fee) esta separada del transporte HTTP a
proposito: eso es lo que permite probarla con una prueba unitaria rapida
(sin base de datos, sin red) mientras que /pay se prueba con una prueba de
integracion contra un Postgres real, tal como describe el post.
"""
import os
import time

import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/payments"
)


def calculate_fee(amount: float) -> float:
    """Logica de negocio pura: comision del 2% con minimo de 0.30."""
    if amount <= 0:
        raise ValueError("amount debe ser positivo")
    return round(max(amount * 0.02, 0.30), 2)


def get_connection(retries: int = 10, delay: float = 1.0):
    last_error = None
    for _ in range(retries):
        try:
            return psycopg2.connect(DATABASE_URL)
        except psycopg2.OperationalError as exc:
            last_error = exc
            time.sleep(delay)
    raise last_error


def init_db() -> None:
    conn = get_connection()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS payments (
                    id SERIAL PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    amount NUMERIC NOT NULL,
                    fee NUMERIC NOT NULL,
                    status TEXT NOT NULL
                )
                """
            )
    finally:
        conn.close()


@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/pay", methods=["POST"])
def pay():
    payload = request.get_json(force=True, silent=True) or {}
    amount = payload.get("amount")
    customer_id = payload.get("customer_id")

    if amount is None or customer_id is None:
        return jsonify(error="amount y customer_id son requeridos"), 400

    try:
        fee = calculate_fee(float(amount))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    conn = get_connection()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO payments (customer_id, amount, fee, status) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (customer_id, amount, fee, "completed"),
            )
            payment_id = cur.fetchone()[0]
    finally:
        conn.close()

    # Este es el "contrato" que el servicio proveedor promete a sus
    # consumidores: los campos y tipos que devuelve /pay.
    return jsonify(
        id=payment_id,
        customer_id=customer_id,
        amount=amount,
        fee=fee,
        status="completed",
    )


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)
