"""
Mini pipeline de "AI Operations": genera metricas sinteticas de un servicio,
las procesa con feature engineering (MetricsProcessor) y detecta anomalias
con Isolation Forest (AnomalyDetector), replicando el flujo descripto en el
post "AI/ML en Operaciones IT".

Ejecucion: python3 ai_ops_pipeline.py
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class MetricsProcessor:
    """Normaliza metricas crudas y calcula caracteristicas derivadas
    (capa de 'procesamiento' del post: feature engineering sobre
    series temporales de CPU, memoria y requests)."""

    def __init__(self):
        self.scaler = StandardScaler()

    def process_metrics(self, raw_metrics):
        df = pd.DataFrame(raw_metrics)

        # Caracteristicas derivadas
        df["cpu_trend"] = df["cpu_usage"].rolling(window=10, min_periods=1).mean()
        df["memory_spike"] = df["memory_usage"].diff().fillna(0)
        df["request_rate_change"] = df["requests_per_sec"].pct_change().fillna(0)

        # Deteccion de anomalias basica (heuristica, previa al modelo ML)
        memory_std = df["memory_usage"].std() or 1.0
        df["is_anomaly_heuristic"] = (
            (df["cpu_usage"] > df["cpu_trend"] * 1.5)
            | (df["memory_spike"].abs() > memory_std * 2)
        )

        return df


class AnomalyDetector:
    """Detector de anomalias con Isolation Forest, entrenado sobre
    comportamiento normal e inferido sobre metricas nuevas."""

    def __init__(self, contamination=0.1):
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
        )
        self.feature_cols = ["cpu_usage", "memory_usage", "requests_per_sec"]

    def train(self, historical_metrics: pd.DataFrame):
        self.model.fit(historical_metrics[self.feature_cols])

    def detect(self, current_metrics: pd.DataFrame):
        features = current_metrics[self.feature_cols]

        # -1 anomalia, 1 normal
        predictions = self.model.predict(features)
        scores = self.model.score_samples(features)

        return {
            "is_anomaly": predictions == -1,
            "anomaly_score": -scores,  # mayor = mas anomalo
            "threshold": np.percentile(-scores, 90),
        }


def generar_metricas_sinteticas(n_normal=200, n_anomalas=10, seed=42):
    """Simula metricas de un servicio: comportamiento normal (CPU/memoria
    estables con ruido) mas un puñado de picos anomalos (fuga de memoria /
    saturacion de CPU), para poder entrenar y despues detectar."""
    rng = np.random.default_rng(seed)

    normal = pd.DataFrame(
        {
            "cpu_usage": rng.normal(loc=35, scale=5, size=n_normal).clip(0, 100),
            "memory_usage": rng.normal(loc=50, scale=4, size=n_normal).clip(0, 100),
            "requests_per_sec": rng.normal(loc=120, scale=15, size=n_normal).clip(0),
        }
    )

    anomalas = pd.DataFrame(
        {
            "cpu_usage": rng.uniform(85, 99, size=n_anomalas),
            "memory_usage": rng.uniform(90, 99, size=n_anomalas),
            "requests_per_sec": rng.uniform(5, 20, size=n_anomalas),
        }
    )

    df = pd.concat([normal, anomalas], ignore_index=True)
    df["is_synthetic_anomaly"] = [False] * n_normal + [True] * n_anomalas
    return df.sample(frac=1, random_state=seed).reset_index(drop=True)


def main():
    print("=" * 70)
    print("1) GENERACION DE METRICAS SINTETICAS")
    print("=" * 70)
    dataset = generar_metricas_sinteticas()
    print(f"Total de muestras: {len(dataset)}")
    print(f"Anomalas inyectadas (ground truth): {dataset['is_synthetic_anomaly'].sum()}")

    print()
    print("=" * 70)
    print("2) PROCESAMIENTO DE METRICAS (MetricsProcessor)")
    print("=" * 70)
    processor = MetricsProcessor()
    processed = processor.process_metrics(dataset)
    print(processed[["cpu_usage", "memory_usage", "cpu_trend", "memory_spike"]].head(5))

    print()
    print("=" * 70)
    print("3) ENTRENAMIENTO Y DETECCION (AnomalyDetector / Isolation Forest)")
    print("=" * 70)
    # Entrenamos solo con el comportamiento "normal" (simula datos historicos
    # sin incidentes), tal como describe el post.
    detector = AnomalyDetector(contamination=0.05)
    train_data = dataset[~dataset["is_synthetic_anomaly"]]
    detector.train(train_data)

    resultado = detector.detect(dataset)
    dataset["is_anomaly_ml"] = resultado["is_anomaly"]
    dataset["anomaly_score"] = resultado["anomaly_score"]

    detectadas = dataset[dataset["is_anomaly_ml"]]
    print(f"Umbral de score (percentil 90): {resultado['threshold']:.4f}")
    print(f"Anomalias detectadas por el modelo: {len(detectadas)}")
    print()
    print(
        detectadas[
            ["cpu_usage", "memory_usage", "requests_per_sec", "anomaly_score", "is_synthetic_anomaly"]
        ]
        .sort_values("anomaly_score", ascending=False)
        .head(10)
        .to_string(index=False)
    )

    print()
    print("=" * 70)
    print("4) EVALUACION CONTRA GROUND TRUTH")
    print("=" * 70)
    verdaderos_positivos = int(
        ((dataset["is_anomaly_ml"]) & (dataset["is_synthetic_anomaly"])).sum()
    )
    total_anomalas_reales = int(dataset["is_synthetic_anomaly"].sum())
    print(
        f"El modelo detecto {verdaderos_positivos} de {total_anomalas_reales} "
        "anomalias inyectadas (picos de CPU/memoria con caida de trafico)."
    )


if __name__ == "__main__":
    main()
