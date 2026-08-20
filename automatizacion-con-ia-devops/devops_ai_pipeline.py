#!/usr/bin/env python3
"""
Mini pipeline de "AI DevOps" basado en los dos componentes que describe el post:

1. Capa de normalizacion de datos: unifica logs de distintas fuentes/formatos
   en una estructura consistente (igual que DevOpsDataNormalizer del post).
2. Motor de analisis predictivo: aplica la heuristica del post (CPU > 75%
   sostenido + aumento de latencia => alta probabilidad de fallo del servicio
   en los proximos minutos) sobre una serie de metricas, y correlaciona el
   resultado con los errores ya detectados en los logs normalizados.

No requiere API keys ni servicios externos: todo corre en local con datos
de ejemplo (sample_logs.json, sample_metrics.csv).
"""
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent

SEVERITY_MAP = {
    "DEBUG": "debug",
    "INFO": "info",
    "WARN": "warning",
    "WARNING": "warning",
    "ERROR": "error",
    "CRITICAL": "critical",
}

CPU_THRESHOLD = 75.0
LATENCY_INCREASE_PCT = 30.0
FAILURE_PROBABILITY_WHEN_TRIGGERED = 0.85


class DevOpsDataNormalizer:
    """Normaliza logs de multiples fuentes/formatos a una estructura estandar."""

    def normalize_logs(self, raw_logs):
        normalized = []
        for log in raw_logs:
            normalized.append(
                {
                    "timestamp": self.parse_timestamp(log.get("time")),
                    "severity": self.map_severity(log.get("level")),
                    "service": log.get("service", "unknown"),
                    "message": log.get("msg", ""),
                }
            )
        return pd.DataFrame(normalized)

    def parse_timestamp(self, time_str):
        formats = ["%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"]
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except (ValueError, TypeError):
                continue
        return None

    def map_severity(self, level):
        if not level:
            return "unknown"
        return SEVERITY_MAP.get(level.upper(), "unknown")


class PredictiveFailureEngine:
    """
    Implementa la heuristica descripta en el post:
    CPU > 75% sostenido + aumento de latencia >= 30% respecto de la linea
    base => probabilidad alta de fallo del servicio en los proximos minutos.
    """

    def __init__(self, cpu_threshold=CPU_THRESHOLD, latency_increase_pct=LATENCY_INCREASE_PCT):
        self.cpu_threshold = cpu_threshold
        self.latency_increase_pct = latency_increase_pct

    def analyze(self, metrics_df):
        baseline_latency = metrics_df["latency_ms"].iloc[:5].mean()
        alerts = []
        for _, row in metrics_df.iterrows():
            latency_increase = ((row["latency_ms"] - baseline_latency) / baseline_latency) * 100
            cpu_high = row["cpu_pct"] > self.cpu_threshold
            latency_spike = latency_increase >= self.latency_increase_pct
            if cpu_high and latency_spike:
                alerts.append(
                    {
                        "seconds_offset": row["seconds_offset"],
                        "service": row["service"],
                        "cpu_pct": row["cpu_pct"],
                        "latency_ms": row["latency_ms"],
                        "latency_increase_pct": round(latency_increase, 1),
                        "failure_probability": FAILURE_PROBABILITY_WHEN_TRIGGERED,
                    }
                )
        return alerts


def load_raw_logs(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_metrics(path):
    return pd.read_csv(path)


def correlate_errors_with_prediction(normalized_logs_df, first_alert):
    if first_alert is None:
        return pd.DataFrame()
    errors = normalized_logs_df[normalized_logs_df["severity"].isin(["error", "critical"])]
    return errors[errors["service"] == first_alert["service"]]


def main():
    logs_path = BASE_DIR / "sample_logs.json"
    metrics_path = BASE_DIR / "sample_metrics.csv"

    print("=" * 70)
    print("1) NORMALIZACION DE LOGS")
    print("=" * 70)
    raw_logs = load_raw_logs(logs_path)
    normalizer = DevOpsDataNormalizer()
    normalized_df = normalizer.normalize_logs(raw_logs)
    print(f"Logs crudos: {len(raw_logs)} (formatos de timestamp mixtos)")
    print(f"Logs normalizados: {len(normalized_df)}")
    print(normalized_df.to_string(index=False))

    print()
    print("=" * 70)
    print("2) MOTOR DE ANALISIS PREDICTIVO")
    print("=" * 70)
    metrics_df = load_metrics(metrics_path)
    engine = PredictiveFailureEngine()
    alerts = engine.analyze(metrics_df)

    if not alerts:
        print("No se detectaron condiciones de fallo predictivo en la ventana analizada.")
        sys.exit(0)

    first_alert = alerts[0]
    print(f"Se detectaron {len(alerts)} puntos en la ventana con condicion de riesgo.")
    print("Primer punto donde se dispara la prediccion:")
    for k, v in first_alert.items():
        print(f"  {k}: {v}")

    print()
    print("=" * 70)
    print("3) CORRELACION CON LOGS DE ERROR (mismo servicio)")
    print("=" * 70)
    correlated = correlate_errors_with_prediction(normalized_df, first_alert)
    if correlated.empty:
        print("No hay logs de error correlacionados para ese servicio.")
    else:
        print(correlated.to_string(index=False))
        print()
        print(
            f"CONCLUSION: el motor predictivo marco a '{first_alert['service']}' con "
            f"{first_alert['failure_probability'] * 100:.0f}% de probabilidad de fallo "
            f"({first_alert['cpu_pct']}% CPU, +{first_alert['latency_increase_pct']}% latencia) "
            f"y los logs confirman {len(correlated)} eventos error/critical en ese mismo servicio: "
            "el patron descripto en el post se reproduce con datos locales."
        )


if __name__ == "__main__":
    main()
