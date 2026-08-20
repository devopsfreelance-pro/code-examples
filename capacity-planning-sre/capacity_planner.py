#!/usr/bin/env python3
"""
Mini capacity planner para SRE.

Reproduce, con datos sintéticos pero reproducibles, el flujo central del post:

1. Recolección de métricas de capacidad (CapacityMetric / CapacityCollector).
2. Clasificación en zonas de umbral verde/amarillo/naranja/rojo.
3. Forecasting con regresión lineal + features cíclicas (hora, día de semana),
   igual que el CapacityForecaster del post.
4. Estimación de "días hasta capacidad crítica" a partir del forecast, que es
   la pregunta que responde el capacity planning: ¿cuándo necesito escalar?

No requiere infraestructura: genera sus propios datos históricos simulados
(30 días de utilización de CPU con tendencia + estacionalidad diaria + ruido)
y corre en segundos con solo `pandas`, `numpy` y `scikit-learn`.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

RANDOM_SEED = 42
HISTORY_DAYS = 30
FORECAST_DAYS = 14
CRITICAL_THRESHOLD = 90.0
PREVENTIVE_THRESHOLD = 80.0
WARNING_THRESHOLD = 70.0


@dataclass
class CapacityMetric:
    timestamp: datetime
    resource_type: str
    utilization_percent: float
    service_name: str

    def headroom_percent(self) -> float:
        """Calcula el margen de capacidad disponible."""
        return 100 - self.utilization_percent

    def zone(self) -> str:
        """Clasifica la métrica en la zona de umbral del post
        (verde/amarillo/naranja/rojo)."""
        if self.utilization_percent >= CRITICAL_THRESHOLD:
            return "rojo"
        if self.utilization_percent >= PREVENTIVE_THRESHOLD:
            return "naranja"
        if self.utilization_percent >= WARNING_THRESHOLD:
            return "amarillo"
        return "verde"


class CapacityCollector:
    """Simula la recolección histórica de métricas de un servicio con
    crecimiento orgánico y estacionalidad diaria (más carga en horario
    laboral), como describe la sección "Recolección y Análisis de Métricas"
    del post."""

    def __init__(self, service_name: str, seed: int = RANDOM_SEED):
        self.service_name = service_name
        self._rng = np.random.default_rng(seed)

    def collect_history(self, days: int = HISTORY_DAYS) -> list[CapacityMetric]:
        start = datetime.now(timezone.utc) - timedelta(days=days)
        hours = days * 24
        metrics: list[CapacityMetric] = []

        for h in range(hours):
            ts = start + timedelta(hours=h)
            day_progress = h / hours

            # Tendencia de crecimiento: sube ~25 puntos de utilización en
            # todo el periodo (crecimiento orgánico de tráfico).
            trend = 35 + 25 * day_progress

            # Estacionalidad diaria: pico en horario laboral (10-18h UTC).
            daily = 12 * np.sin((ts.hour - 6) / 24 * 2 * np.pi)

            noise = self._rng.normal(0, 3)
            utilization = float(np.clip(trend + daily + noise, 1, 100))

            metrics.append(
                CapacityMetric(
                    timestamp=ts,
                    resource_type="cpu",
                    utilization_percent=utilization,
                    service_name=self.service_name,
                )
            )
        return metrics


class CapacityForecaster:
    """Modelo de forecasting con regresión lineal y features cíclicas,
    equivalente al del post pero recortado a lo esencial para que corra en
    segundos sin dependencias externas."""

    def __init__(self, historical_data: pd.DataFrame):
        self.data = historical_data
        self.model = LinearRegression()
        self.features = [
            "days_since_start",
            "hour_sin",
            "hour_cos",
            "day_sin",
            "day_cos",
        ]

    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["day_of_week"] = df["timestamp"].dt.dayofweek
        df["hour_of_day"] = df["timestamp"].dt.hour
        df["days_since_start"] = (
            df["timestamp"] - self.data["timestamp"].min()
        ).dt.total_seconds() / 86400

        df["hour_sin"] = np.sin(2 * np.pi * df["hour_of_day"] / 24)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour_of_day"] / 24)
        df["day_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
        df["day_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
        return df

    def train(self, target_metric: str = "utilization_percent") -> float:
        df = self._prepare_features(self.data)
        self.model.fit(df[self.features], df[target_metric])
        return self.model.score(df[self.features], df[target_metric])

    def forecast(self, periods_ahead_hours: int) -> pd.DataFrame:
        last_date = self.data["timestamp"].max()
        future_dates = pd.date_range(
            start=last_date, periods=periods_ahead_hours + 1, freq="h"
        )[1:]

        future_df = pd.DataFrame({"timestamp": future_dates})
        future_df = self._prepare_features(future_df)
        future_df["predicted_utilization"] = self.model.predict(
            future_df[self.features]
        )
        return future_df[["timestamp", "predicted_utilization"]]


def days_until_threshold(forecast_df: pd.DataFrame, threshold: float) -> float | None:
    """Primer momento del forecast en que la utilización proyectada cruza
    el umbral dado, expresado en días desde ahora."""
    hits = forecast_df[forecast_df["predicted_utilization"] >= threshold]
    if hits.empty:
        return None
    first_hit = hits.iloc[0]["timestamp"]
    now = forecast_df["timestamp"].min()
    return (first_hit - now).total_seconds() / 86400


def main() -> int:
    service_name = "api-service"

    # 1. Recolección de métricas históricas
    collector = CapacityCollector(service_name)
    history = collector.collect_history(HISTORY_DAYS)
    history_df = pd.DataFrame(
        [
            {"timestamp": m.timestamp, "utilization_percent": m.utilization_percent}
            for m in history
        ]
    )

    # 2. Estado actual y zonas de umbral
    current = history[-1]
    zone_counts = pd.Series([m.zone() for m in history]).value_counts()

    print("=== Estado actual de capacidad ===")
    print(f"Servicio: {current.service_name} (recurso: {current.resource_type})")
    print(f"Utilización actual: {current.utilization_percent:.1f}%")
    print(f"Headroom actual: {current.headroom_percent():.1f}%")
    print(f"Zona actual: {current.zone()}")
    print()
    print("=== Distribución de zonas en los últimos", HISTORY_DAYS, "días ===")
    for zone in ["verde", "amarillo", "naranja", "rojo"]:
        count = int(zone_counts.get(zone, 0))
        pct = 100 * count / len(history)
        print(f"  {zone:9s}: {count:4d} horas ({pct:5.1f}%)")

    # 3. Forecasting
    forecaster = CapacityForecaster(history_df)
    r2 = forecaster.train()
    forecast_df = forecaster.forecast(FORECAST_DAYS * 24)

    print()
    print(f"=== Forecast a {FORECAST_DAYS} días (R^2 del modelo: {r2:.3f}) ===")
    print(
        f"Utilización proyectada al final del periodo: "
        f"{forecast_df.iloc[-1]['predicted_utilization']:.1f}%"
    )

    # 4. Días hasta cada umbral: la pregunta que responde el capacity planning
    print()
    print("=== Días hasta cruzar cada umbral (según forecast) ===")
    for label, threshold in [
        ("amarillo (atención)", WARNING_THRESHOLD),
        ("naranja (escalado preventivo)", PREVENTIVE_THRESHOLD),
        ("rojo (crítico)", CRITICAL_THRESHOLD),
    ]:
        days = days_until_threshold(forecast_df, threshold)
        if days is None:
            print(f"  {label:32s}: no se alcanza en los próximos {FORECAST_DAYS} días")
        else:
            print(f"  {label:32s}: {days:5.1f} días")

    days_to_preventive = days_until_threshold(forecast_df, PREVENTIVE_THRESHOLD)
    print()
    if days_to_preventive is not None and days_to_preventive <= 7:
        print(
            f"ACCION: el forecast cruza el umbral de escalado preventivo "
            f"({PREVENTIVE_THRESHOLD:.0f}%) en {days_to_preventive:.1f} días. "
            "Iniciar pedido de cuota / capacidad adicional ahora."
        )
    else:
        print(
            "OK: no se proyecta necesidad de escalado preventivo dentro de "
            "los próximos 7 días."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
