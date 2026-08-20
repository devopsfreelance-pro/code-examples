#!/usr/bin/env python3
"""
Simulador de nodo edge (gateway de fabrica).

Genera lecturas de un sensor de vibracion/temperatura, ejecuta deteccion
de anomalias LOCALMENTE (sin depender de la nube) y expone las metricas
en formato Prometheus para que el Prometheus del propio nodo edge las
recolecte. Este es el patron central del post: procesar donde se generan
los datos y publicar solo agregados/alertas hacia el nivel central.
"""
import random
import time

from prometheus_client import Counter, Gauge, start_http_server

VIBRATION_BASELINE = 2.0
TEMPERATURE_BASELINE = 45.0
ANOMALY_PROBABILITY = 0.08

sensor_vibration = Gauge(
    "edge_sensor_vibration_mm_s",
    "Vibracion medida en el sensor edge (mm/s)",
    ["machine_id"],
)
sensor_temperature = Gauge(
    "edge_sensor_temperature_celsius",
    "Temperatura medida en el sensor edge (C)",
    ["machine_id"],
)
anomalies_detected_total = Counter(
    "edge_anomalies_detected_total",
    "Anomalias detectadas y resueltas localmente en el nodo edge",
    ["machine_id"],
)
readings_processed_total = Counter(
    "edge_readings_processed_total",
    "Lecturas de sensores procesadas localmente en el nodo edge",
    ["machine_id"],
)

MACHINES = ["line-01", "line-02"]


def read_sensor(machine_id: str) -> tuple[float, float]:
    """Simula una lectura de sensor, con anomalias ocasionales."""
    is_anomaly = random.random() < ANOMALY_PROBABILITY
    if is_anomaly:
        vibration = VIBRATION_BASELINE * random.uniform(3, 6)
        temperature = TEMPERATURE_BASELINE * random.uniform(1.2, 1.5)
    else:
        vibration = VIBRATION_BASELINE + random.uniform(-0.3, 0.3)
        temperature = TEMPERATURE_BASELINE + random.uniform(-2, 2)
    return vibration, temperature, is_anomaly


def detect_anomaly(vibration: float, temperature: float) -> bool:
    """Deteccion simple basada en umbrales, ejecutada en el propio edge."""
    return vibration > VIBRATION_BASELINE * 2.5 or temperature > TEMPERATURE_BASELINE * 1.15


def main() -> None:
    start_http_server(9100)
    print("Nodo edge escuchando metricas en :9100/metrics")
    while True:
        for machine_id in MACHINES:
            vibration, temperature, _ = read_sensor(machine_id)
            sensor_vibration.labels(machine_id=machine_id).set(vibration)
            sensor_temperature.labels(machine_id=machine_id).set(temperature)
            readings_processed_total.labels(machine_id=machine_id).inc()

            if detect_anomaly(vibration, temperature):
                anomalies_detected_total.labels(machine_id=machine_id).inc()
                print(
                    f"[EDGE] anomalia detectada localmente en {machine_id}: "
                    f"vibracion={vibration:.2f}mm/s temperatura={temperature:.1f}C"
                )
        time.sleep(2)


if __name__ == "__main__":
    main()
