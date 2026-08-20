"""
Mini servicio de pagos instrumentado con Datadog APM (ddtrace).

Ilustra el concepto central del post: como una app envia trazas
distribuidas al Datadog Agent, que las reenvia a la plataforma para
correlacionar metricas, trazas y logs en una vista unificada.
"""
import random
import time

from ddtrace import tracer
from flask import Flask, jsonify, request

app = Flask(__name__)


def validate_credit_card(user_id: str) -> None:
    with tracer.trace("validate_card", service="payment-service", resource="validate_credit_card"):
        # Simula latencia de validacion contra un proveedor externo
        time.sleep(random.uniform(0.01, 0.05))
        tracer.current_span().set_tag("user.id", user_id)


def charge_customer(amount: float, user_id: str) -> dict:
    with tracer.trace("charge_amount", service="payment-service", resource="charge_customer") as span:
        span.set_tag("payment.amount", amount)
        span.set_tag("user.id", user_id)
        # Simula la llamada a una pasarela de pago
        time.sleep(random.uniform(0.02, 0.08))
        if amount <= 0:
            span.set_tag("error", True)
            raise ValueError("El monto debe ser mayor a 0")
        return {"status": "approved", "amount": amount, "user_id": user_id}


@tracer.wrap(service="payment-service", resource="process_payment")
def process_payment(amount: float, user_id: str) -> dict:
    validate_credit_card(user_id)
    result = charge_customer(amount, user_id)
    return result


@app.route("/pay", methods=["POST"])
def pay():
    data = request.get_json(force=True) or {}
    amount = float(data.get("amount", 0))
    user_id = str(data.get("user_id", "anonimo"))

    try:
        result = process_payment(amount, user_id)
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"status": "rejected", "error": str(exc)}), 400


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
