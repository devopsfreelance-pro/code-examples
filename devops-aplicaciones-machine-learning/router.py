"""
Router de despliegue canary para model deployment (MLOps DevOps).

Distribuye el trafico de inferencia entre el modelo estable (v1) y el
modelo candidato (v2) segun un porcentaje configurable (CANARY_WEIGHT).
Ademas acumula metricas basicas por version para decidir si el canary
se promueve a estable o se revierte, que es la logica central detras
de las estrategias de despliegue canary y blue-green descriptas en el
post.
"""
import os
import random

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

MODEL_V1_URL = os.environ.get("MODEL_V1_URL", "http://model-v1:5000")
MODEL_V2_URL = os.environ.get("MODEL_V2_URL", "http://model-v2:5000")
# Porcentaje (0-100) de trafico que se envia al modelo candidato (v2).
CANARY_WEIGHT = float(os.environ.get("CANARY_WEIGHT", "10"))

metrics = {
    "v1": {"requests": 0, "predictions_positive": 0},
    "v2": {"requests": 0, "predictions_positive": 0},
}


@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok", canary_weight=CANARY_WEIGHT), 200


@app.route("/predict", methods=["POST"])
def predict():
    payload = request.get_json(silent=True) or {}

    use_canary = random.uniform(0, 100) < CANARY_WEIGHT
    target_url = MODEL_V2_URL if use_canary else MODEL_V1_URL
    version_key = "v2" if use_canary else "v1"

    try:
        response = requests.post(f"{target_url}/predict", json=payload, timeout=2)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        return jsonify(error=f"modelo {version_key} no disponible: {exc}"), 502

    metrics[version_key]["requests"] += 1
    if data.get("prediction") == 1:
        metrics[version_key]["predictions_positive"] += 1

    data["routed_to"] = version_key
    return jsonify(data), 200


@app.route("/metrics", methods=["GET"])
def get_metrics():
    """
    Expone tasas de prediccion positiva por version, la senal minima
    que un pipeline de CI/CD usaria para decidir si promueve el canary
    (por ejemplo, si v2 no degrada la tasa respecto a v1).
    """
    report = {}
    for version, data in metrics.items():
        total = data["requests"]
        rate = round(data["predictions_positive"] / total, 3) if total else None
        report[version] = {
            "requests": total,
            "positive_rate": rate,
        }
    return jsonify(canary_weight=CANARY_WEIGHT, metrics=report), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
