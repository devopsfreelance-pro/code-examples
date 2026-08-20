"""API demo minima para probar performance testing con k6.

Expone dos endpoints:
- GET /products: responde rapido (~10-30ms).
- GET /checkout: simula una operacion mas lenta (~150-400ms) para que el
  test de carga muestre diferencias de latencia entre endpoints.
"""
import random
import time

from flask import Flask, jsonify

app = Flask(__name__)

PRODUCTS = [
    {"id": 1, "name": "Teclado mecanico", "price": 45000},
    {"id": 2, "name": "Mouse inalambrico", "price": 18000},
    {"id": 3, "name": "Monitor 27 pulgadas", "price": 210000},
]


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/products")
def products():
    time.sleep(random.uniform(0.01, 0.03))
    return jsonify(PRODUCTS)


@app.get("/checkout")
def checkout():
    time.sleep(random.uniform(0.15, 0.40))
    return jsonify({"order_id": random.randint(1000, 9999), "status": "confirmed"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
