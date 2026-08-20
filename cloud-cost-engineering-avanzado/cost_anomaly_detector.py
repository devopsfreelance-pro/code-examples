"""
Mini ejemplo ejecutable de cost anomaly detection.

Reimplementa, en version reducida pero funcional, las dos piezas centrales
que describe el post "Cloud Cost Engineering Avanzado":

1. Un pipeline que normaliza datos de costo diario por servicio (en el post
   esto viene de AWS Cost Explorer via boto3; aca se genera un dataset
   sintetico reproducible para no depender de credenciales cloud).
2. Un detector de anomalias que combina dos tecnicas mencionadas en el post:
   - Isolation Forest (sklearn.ensemble.IsolationForest), igual que el
     snippet `detect_cost_anomalies` del post.
   - Desviacion estandar sobre la linea base historica (z-score), la otra
     tecnica que el post menciona como complementaria a los modelos de
     series temporales tipo ARIMA/Prophet.

No requiere cuentas AWS/Azure/GCP: los datos de costo son sinteticos, con
una anomalia inyectada a proposito para poder verificar que el detector la
encuentra.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

RANDOM_SEED = 42


def generate_synthetic_cost_data(days: int = 60) -> pd.DataFrame:
    """
    Genera costos diarios sinteticos para un servicio (equivalente a un
    grupo `GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]` del post),
    con tendencia leve, estacionalidad semanal y ruido.

    Inyecta una anomalia real el dia 45: el gasto se dispara de ~500 a
    ~5000 USD, igual al ejemplo textual que usa el post
    ("si un servicio que normalmente consume 500 dolares diarios
    subitamente genera un gasto de 5,000 dolares").
    """
    rng = np.random.default_rng(RANDOM_SEED)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=days)

    base_cost = 500.0
    trend = np.linspace(0, 40, days)  # crecimiento organico leve
    weekly_seasonality = 60 * np.sin(np.arange(days) * (2 * np.pi / 7))
    noise = rng.normal(0, 25, days)

    daily_cost = base_cost + trend + weekly_seasonality + noise
    resource_count = rng.integers(18, 32, days).astype(float)
    cpu_hours = daily_cost / 5 + rng.normal(0, 5, days)

    df = pd.DataFrame(
        {
            "date": dates,
            "daily_cost": daily_cost,
            "resource_count": resource_count,
            "cpu_hours": cpu_hours,
        }
    )

    # Anomalia inyectada: pico de gasto sin justificacion en recursos/cpu.
    anomaly_idx = days - 15
    df.loc[anomaly_idx, "daily_cost"] = 5000.0

    return df


def detect_cost_anomalies_isolation_forest(cost_data: pd.DataFrame) -> pd.DataFrame:
    """
    Misma logica que el snippet `detect_cost_anomalies` del post, aplicada
    al dataset sintetico.
    """
    features = cost_data[["daily_cost", "resource_count", "cpu_hours"]]

    model = IsolationForest(contamination=0.1, random_state=RANDOM_SEED)
    predictions = model.fit_predict(features)

    anomalies = cost_data[predictions == -1].copy()
    return anomalies


def detect_cost_anomalies_zscore(cost_data: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
    """
    Segunda tecnica que menciona el post: analisis de desviacion estandar
    sobre la linea base historica (z-score) como complemento al modelo de
    ML, util para explicar de forma simple por que algo fue marcado.
    """
    mean = cost_data["daily_cost"].mean()
    std = cost_data["daily_cost"].std()

    z_scores = (cost_data["daily_cost"] - mean) / std
    flagged = cost_data[z_scores.abs() > threshold].copy()
    flagged["z_score"] = z_scores[z_scores.abs() > threshold]

    return flagged


def main() -> None:
    cost_data = generate_synthetic_cost_data(days=60)

    print(f"Dataset generado: {len(cost_data)} dias, "
          f"costo diario promedio ${cost_data['daily_cost'].mean():.2f}\n")

    iso_anomalies = detect_cost_anomalies_isolation_forest(cost_data)
    print(f"Isolation Forest detecto {len(iso_anomalies)} anomalia(s):")
    print(iso_anomalies[["date", "daily_cost", "resource_count", "cpu_hours"]]
          .to_string(index=False))

    print()

    zscore_anomalies = detect_cost_anomalies_zscore(cost_data)
    print(f"Z-score (umbral 3.0) detecto {len(zscore_anomalies)} anomalia(s):")
    print(zscore_anomalies[["date", "daily_cost", "z_score"]]
          .to_string(index=False))


if __name__ == "__main__":
    main()
