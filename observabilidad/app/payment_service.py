"""Servicio "payment-service": recibe la validacion de pago.

Servicio downstream de la traza distribuida. Expone /validate-payment
y crea un span manual para simular la logica de validacion, tal como
muestra el post en el ejemplo de OpenTelemetry + Flask.
"""
import random
import time

from flask import Flask, jsonify
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.trace import Status, StatusCode

from tracing_setup import setup_tracing

tracer = setup_tracing(service_name="payment-service")

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)


@app.route("/validate-payment")
def validate_payment():
    with tracer.start_as_current_span("validate-payment-details") as span:
        span.set_attribute("payment.amount", 150.00)
        span.set_attribute("payment.currency", "USD")

        # Simula trabajo real (ej: llamada a una pasarela de pago)
        time.sleep(random.uniform(0.05, 0.2))
        validation_ok = random.random() > 0.2

        if validation_ok:
            span.set_attribute("validation.status", "success")
        else:
            span.set_attribute("validation.status", "failed")
            span.set_status(Status(StatusCode.ERROR, "Validation failed"))

    return jsonify({"validated": validation_ok})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
