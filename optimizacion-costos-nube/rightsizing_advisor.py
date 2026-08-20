#!/usr/bin/env python3
"""
rightsizing_advisor.py

Analiza metricas de utilizacion de CPU (formato similar a CloudWatch
GetMetricStatistics) y genera recomendaciones de rightsizing, mostrando
cuanto se ahorraria (o costaria) el cambio bajo tres modelos de compra:
On-Demand, Reserved Instance (1 anio) e Instancia Spot.

Ilustra en miniatura las tres estrategias del post "Optimizar costos cloud":
- Rightsizing (dimensionamiento correcto segun uso real de CPU)
- Instancias reservadas / Savings Plans
- Instancias spot

No requiere cuenta de AWS ni credenciales: opera sobre un CSV local con
metricas de ejemplo (sample_cpu_metrics.csv) y una tabla de precios de
referencia (pricing_table.json).

Uso:
    python3 rightsizing_advisor.py sample_cpu_metrics.csv pricing_table.json
    python3 rightsizing_advisor.py sample_cpu_metrics.csv pricing_table.json \
        --low-threshold 20 --low-max-threshold 50 --high-threshold 70
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from statistics import mean

HOURS_PER_MONTH = 730


def cargar_metricas(csv_path):
    """Agrupa las muestras de CPU por instancia y devuelve avg/max por instancia."""
    muestras = defaultdict(list)
    tipos = {}

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            instance_id = row["instance_id"]
            tipos[instance_id] = row["instance_type"]
            muestras[instance_id].append(float(row["cpu_utilization"]))

    resultado = {}
    for instance_id, valores in muestras.items():
        resultado[instance_id] = {
            "instance_type": tipos[instance_id],
            "cpu_promedio": round(mean(valores), 2),
            "cpu_maximo": round(max(valores), 2),
            "muestras": len(valores),
        }
    return resultado


def cargar_pricing(pricing_path):
    with open(pricing_path) as f:
        return json.load(f)


def familia_de(instance_type):
    return instance_type.split(".")[0]


def siguiente_tamano(pricing, instance_type, direccion):
    """direccion: -1 para downsize, +1 para upsize. Devuelve None si no hay tamano disponible."""
    familia = familia_de(instance_type)
    escalera = pricing["size_ladder"].get(familia)
    if not escalera or instance_type not in escalera:
        return None
    idx = escalera.index(instance_type)
    nuevo_idx = idx + direccion
    if nuevo_idx < 0 or nuevo_idx >= len(escalera):
        return None
    return escalera[nuevo_idx]


def recomendar(cpu_promedio, cpu_maximo, low_threshold, low_max_threshold, high_threshold):
    if cpu_promedio < low_threshold and cpu_maximo < low_max_threshold:
        return "DOWNSIZE"
    if cpu_promedio > high_threshold:
        return "UPSIZE"
    return "MANTENER"


def costo_mensual(pricing, instance_type, modelo):
    precio_hora = pricing["instances"][instance_type][modelo]
    return round(precio_hora * HOURS_PER_MONTH, 2)


def analizar(metrics_path, pricing_path, low_threshold, low_max_threshold, high_threshold):
    metricas = cargar_metricas(metrics_path)
    pricing = cargar_pricing(pricing_path)

    print("=" * 72)
    print("RIGHTSIZING ADVISOR - analisis de utilizacion de CPU")
    print("=" * 72)

    ahorro_total_downsize = 0.0
    costo_total_actual_ondemand = 0.0
    costo_total_recomendado_ondemand = 0.0

    for instance_id in sorted(metricas):
        info = metricas[instance_id]
        tipo_actual = info["instance_type"]
        recomendacion = recomendar(
            info["cpu_promedio"], info["cpu_maximo"],
            low_threshold, low_max_threshold, high_threshold,
        )

        if tipo_actual not in pricing["instances"]:
            print(f"\n{instance_id} ({tipo_actual}): sin datos de precio, se omite.")
            continue

        costo_actual = costo_mensual(pricing, tipo_actual, "on_demand")
        costo_total_actual_ondemand += costo_actual

        print(f"\n{instance_id}  [{tipo_actual}]")
        print(f"  CPU promedio: {info['cpu_promedio']}%  |  CPU maximo: {info['cpu_maximo']}%  "
              f"({info['muestras']} muestras)")
        print(f"  Recomendacion: {recomendacion}")
        print(f"  Costo On-Demand actual: USD {costo_actual}/mes")

        if recomendacion in ("DOWNSIZE", "UPSIZE"):
            direccion = -1 if recomendacion == "DOWNSIZE" else 1
            tipo_nuevo = siguiente_tamano(pricing, tipo_actual, direccion)
            if tipo_nuevo is None:
                print("  No hay un tamano disponible en esa direccion dentro de la escalera.")
                costo_total_recomendado_ondemand += costo_actual
                continue

            costo_nuevo_ondemand = costo_mensual(pricing, tipo_nuevo, "on_demand")
            costo_nuevo_reserved = costo_mensual(pricing, tipo_nuevo, "reserved_1yr")
            costo_nuevo_spot = costo_mensual(pricing, tipo_nuevo, "spot_avg")
            costo_total_recomendado_ondemand += costo_nuevo_ondemand

            delta = round(costo_actual - costo_nuevo_ondemand, 2)
            if recomendacion == "DOWNSIZE":
                ahorro_total_downsize += max(delta, 0)

            print(f"  Tipo sugerido: {tipo_nuevo}")
            print(f"    On-Demand: USD {costo_nuevo_ondemand}/mes  (delta: {delta:+} USD/mes)")
            print(f"    Reserved 1yr: USD {costo_nuevo_reserved}/mes")
            print(f"    Spot (promedio): USD {costo_nuevo_spot}/mes")
        else:
            costo_total_recomendado_ondemand += costo_actual
            costo_reserved = costo_mensual(pricing, tipo_actual, "reserved_1yr")
            costo_spot = costo_mensual(pricing, tipo_actual, "spot_avg")
            print(f"  Alternativa Reserved 1yr (mismo tipo): USD {costo_reserved}/mes")
            print(f"  Alternativa Spot (mismo tipo, si tolera interrupciones): USD {costo_spot}/mes")

    print("\n" + "=" * 72)
    print("RESUMEN")
    print("=" * 72)
    print(f"Costo On-Demand actual (todas las instancias): USD {round(costo_total_actual_ondemand, 2)}/mes")
    print(f"Costo On-Demand tras aplicar recomendaciones:   USD {round(costo_total_recomendado_ondemand, 2)}/mes")
    print(f"Ahorro estimado solo por downsizing:            USD {round(ahorro_total_downsize, 2)}/mes")

    if costo_total_actual_ondemand > 0:
        pct = round((costo_total_actual_ondemand - costo_total_recomendado_ondemand) / costo_total_actual_ondemand * 100, 1)
        print(f"Reduccion neta proyectada sobre el total:       {pct}%")


def main():
    parser = argparse.ArgumentParser(description="Analiza utilizacion de CPU y recomienda rightsizing.")
    parser.add_argument("metrics_csv", help="CSV con columnas instance_id,instance_type,timestamp,cpu_utilization")
    parser.add_argument("pricing_json", help="JSON con la tabla de precios por tipo de instancia")
    parser.add_argument("--low-threshold", type=float, default=20.0,
                         help="Umbral de CPU promedio por debajo del cual se considera DOWNSIZE (default 20)")
    parser.add_argument("--low-max-threshold", type=float, default=50.0,
                         help="Umbral de CPU maximo por debajo del cual se considera DOWNSIZE (default 50)")
    parser.add_argument("--high-threshold", type=float, default=70.0,
                         help="Umbral de CPU promedio por encima del cual se considera UPSIZE (default 70)")
    args = parser.parse_args()

    try:
        analizar(args.metrics_csv, args.pricing_json, args.low_threshold,
                  args.low_max_threshold, args.high_threshold)
    except FileNotFoundError as e:
        print(f"Error: no se encontro el archivo {e.filename}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
