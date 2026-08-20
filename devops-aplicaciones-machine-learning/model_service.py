"""
Servicio de inferencia minimo para simular un modelo de ML desplegado.

Cada instancia representa una version del modelo (v1 o v2). La version y
su "calidad" simulada se controlan via variables de entorno para poder
comparar un modelo estable (v1) contra un modelo candidato (v2) durante
un despliegue canary, tal como describe el post de MLOps DevOps.
"""
import os
import random
import time

from flask import Flask, jsonify, request

app = Flask(__name__)

MODEL_VERSION = os.environ.get("MODEL_VERSION", "v1")
# Probabilidad de que el modelo prediga "correctamente" (simulado).
# v1 = modelo estable ya validado en produccion.
# v2 = modelo candidato, algo mejor, que se despliega como canary.
MODEL_ACCURACY = float(os.environ.get("MODEL_ACCURACY", "0.85"))


@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok", version=MODEL_VERSION), 200


@app.route("/predict", methods=["POST"])
def predict():
    payload = request.get_json(silent=True) or {}
    features = payload.get("features", [])

    # Simulamos latencia de inferencia real.
    time.sleep(0.01)

    # "Prediccion" simulada: acierta segun MODEL_ACCURACY.
    correct = random.random() < MODEL_ACCURACY
    prediction = 1 if correct else 0

    return jsonify(
        model_version=MODEL_VERSION,
        features_received=len(features),
        prediction=prediction,
        confidence=round(random.uniform(0.6, 0.99), 2),
    ), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
