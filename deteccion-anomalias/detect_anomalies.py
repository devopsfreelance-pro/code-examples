#!/usr/bin/env python3
"""
Deteccion de anomalias con Isolation Forest sobre metricas sinteticas.

Simula lo que describe el post: se entrena un detector con datos historicos
"normales" (latencia y uso de CPU de una API) y despues se evalua un lote de
metricas "actuales" que incluye anomalias puntuales inyectadas a proposito
(picos de latencia y de CPU). El script imprime que puntos fueron marcados
como anomalos y su anomaly score.

Uso:
    python detect_anomalies.py
"""

import numpy as np
from sklearn.ensemble import IsolationForest


def generar_metricas_historicas(n_muestras: int = 2000, seed: int = 42) -> np.ndarray:
    """Genera metricas historicas 'normales': latencia (ms) y uso de CPU (%).

    Latencia normal: media 50ms, desvio 8ms.
    CPU normal: media 35%, desvio 10%, acotado a [0, 100].
    """
    rng = np.random.default_rng(seed)
    latencia = rng.normal(loc=50, scale=8, size=n_muestras)
    cpu = np.clip(rng.normal(loc=35, scale=10, size=n_muestras), 0, 100)
    return np.column_stack([latencia, cpu])


def generar_metricas_actuales(n_muestras: int = 200, n_anomalias: int = 8, seed: int = 7):
    """Genera un lote 'actual' con la mayoria de puntos normales y algunas
    anomalias puntuales inyectadas (picos de latencia y/o CPU).

    Devuelve las metricas y los indices donde se inyectaron anomalias reales,
    para poder comparar contra lo que detecta el modelo.
    """
    rng = np.random.default_rng(seed)
    latencia = rng.normal(loc=50, scale=8, size=n_muestras)
    cpu = np.clip(rng.normal(loc=35, scale=10, size=n_muestras), 0, 100)

    indices_anomalos = rng.choice(n_muestras, size=n_anomalias, replace=False)
    for idx in indices_anomalos:
        # Pico de latencia (ej: API que normalmente responde en 50ms tarda ~5s)
        if rng.random() < 0.5:
            latencia[idx] = rng.uniform(300, 800)
        # Saturacion de CPU
        else:
            cpu[idx] = rng.uniform(95, 100)

    metricas = np.column_stack([latencia, cpu])
    return metricas, set(indices_anomalos.tolist())


def main() -> None:
    historicas = generar_metricas_historicas()
    actuales, indices_anomalos_reales = generar_metricas_actuales()

    detector = IsolationForest(
        contamination=0.04,  # ~4% de anomalias esperadas, similar a n_anomalias/n_muestras
        max_samples=256,
        random_state=42,
        n_estimators=100,
    )
    detector.fit(historicas)

    predicciones = detector.predict(actuales)  # -1 = anomalia, 1 = normal
    scores = detector.score_samples(actuales)  # mas negativo = mas anomalo

    indices_detectados = set(np.where(predicciones == -1)[0].tolist())

    print("=== Deteccion de anomalias (Isolation Forest) ===")
    print(f"Metricas historicas usadas para entrenar: {len(historicas)}")
    print(f"Metricas actuales evaluadas: {len(actuales)}")
    print(f"Anomalias inyectadas realmente: {len(indices_anomalos_reales)}")
    print(f"Anomalias detectadas por el modelo: {len(indices_detectados)}")
    print()

    print("idx  | latencia_ms | cpu_%  | score    | inyectada | detectada")
    print("-----|-------------|--------|----------|-----------|----------")
    for idx in sorted(indices_anomalos_reales | indices_detectados):
        latencia, cpu = actuales[idx]
        es_inyectada = idx in indices_anomalos_reales
        es_detectada = idx in indices_detectados
        print(
            f"{idx:4d} | {latencia:11.1f} | {cpu:6.1f} | {scores[idx]:8.4f} "
            f"| {'si' if es_inyectada else 'no':9s} | {'si' if es_detectada else 'no'}"
        )

    verdaderos_positivos = len(indices_anomalos_reales & indices_detectados)
    falsos_negativos = len(indices_anomalos_reales - indices_detectados)
    falsos_positivos = len(indices_detectados - indices_anomalos_reales)

    print()
    print(f"Verdaderos positivos: {verdaderos_positivos}")
    print(f"Falsos negativos:     {falsos_negativos}")
    print(f"Falsos positivos:     {falsos_positivos}")


if __name__ == "__main__":
    main()
