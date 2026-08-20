#!/usr/bin/env python3
"""
Calculadora de eficiencia energetica y huella de carbono de instancias EC2.

Version standalone del script del post (que usa boto3 + CloudWatch en vivo):
en lugar de consultar AWS, lee metricas de un CSV para que el ejemplo sea
100% ejecutable en local, sin cuenta de AWS ni costos.

Aplica los mismos umbrales y formulas del post:
- Umbral de subutilizacion: CPU promedio < 20%
- Factor de emision: 0.5 kg CO2 por kWh (promedio de red electrica)
- Objetivo de sostenibilidad DevOps: factor de utilizacion > 70%
"""
import argparse
import csv
import sys

UMBRAL_SUBUTILIZACION_PCT = 20.0
FACTOR_EMISION_KG_CO2_POR_KWH = 0.5

# Consumo energetico estimado por tipo de instancia (kWh, uso continuo)
CONSUMO_KWH = {
    "t3.medium": 0.025,
    "t3.large": 0.05,
    "m5.large": 0.08,
    "m5.xlarge": 0.16,
}
CONSUMO_KWH_DEFAULT = 0.1


def calcular_huella_carbono(instance_type: str, horas: float) -> float:
    """kg de CO2 emitidos por una instancia durante `horas` de uso."""
    consumo = CONSUMO_KWH.get(instance_type, CONSUMO_KWH_DEFAULT)
    return consumo * FACTOR_EMISION_KG_CO2_POR_KWH * horas


def analizar_instancias(csv_path: str) -> list[dict]:
    recomendaciones = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for fila in reader:
            instance_id = fila["instance_id"]
            instance_type = fila["instance_type"]
            cpu_promedio = float(fila["cpu_promedio_pct"])
            horas = float(fila["horas_encendida_mes"])

            huella_actual = calcular_huella_carbono(instance_type, horas)

            if cpu_promedio < UMBRAL_SUBUTILIZACION_PCT:
                # Downsizing estimado: bajar un escalon de instancia reduce
                # el consumo aproximadamente a la mitad.
                huella_optimizada = huella_actual / 2
                recomendaciones.append(
                    {
                        "instance_id": instance_id,
                        "tipo_actual": instance_type,
                        "cpu_promedio": round(cpu_promedio, 1),
                        "recomendacion": "Considerar downsizing o consolidacion",
                        "huella_actual_kg_co2": round(huella_actual, 2),
                        "ahorro_estimado_kg_co2": round(
                            huella_actual - huella_optimizada, 2
                        ),
                    }
                )

    return recomendaciones


def imprimir_reporte(recomendaciones: list[dict]) -> None:
    if not recomendaciones:
        print("No se detectaron instancias subutilizadas (CPU >= 20% en todas).")
        return

    ahorro_total = sum(r["ahorro_estimado_kg_co2"] for r in recomendaciones)

    print(f"{'instance_id':<22}{'tipo':<12}{'cpu_%':>8}{'ahorro_kgCO2':>15}")
    print("-" * 57)
    for r in recomendaciones:
        print(
            f"{r['instance_id']:<22}{r['tipo_actual']:<12}"
            f"{r['cpu_promedio']:>8}{r['ahorro_estimado_kg_co2']:>15}"
        )

    print("-" * 57)
    print(f"Instancias subutilizadas detectadas: {len(recomendaciones)}")
    print(f"Ahorro estimado total: {round(ahorro_total, 2)} kg CO2/mes")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analiza instancias EC2 y estima ahorro de CO2 por rightsizing."
    )
    parser.add_argument(
        "--csv",
        default="sample_instances.csv",
        help="Ruta al CSV de instancias (default: sample_instances.csv)",
    )
    args = parser.parse_args()

    recomendaciones = analizar_instancias(args.csv)
    imprimir_reporte(recomendaciones)
    return 0


if __name__ == "__main__":
    sys.exit(main())
