#!/usr/bin/env python3
"""
Analiza la distribucion de tiempo del equipo entre toil, trabajo de
ingenieria y trabajo operacional no-toil, a partir de un CSV de tickets.

Uso:
    python3 analizar_toil.py tickets_ejemplo.csv

El CSV debe tener columnas: ticket_id, categoria, horas_invertidas
donde categoria es una de: toil | ingenieria | ops_complejo
"""
import sys

import pandas as pd


def analizar_distribucion_trabajo(tickets_df: pd.DataFrame) -> pd.DataFrame:
    """Analiza la distribucion de tiempo entre toil y trabajo de ingenieria."""
    total_horas = tickets_df["horas_invertidas"].sum()

    distribucion = tickets_df.groupby("categoria").agg(
        horas_invertidas=("horas_invertidas", "sum"),
        cantidad_tickets=("ticket_id", "count"),
    )

    distribucion["porcentaje_tiempo"] = (
        distribucion["horas_invertidas"] / total_horas * 100
    )

    toil_percentage = distribucion.loc["toil", "porcentaje_tiempo"] if "toil" in distribucion.index else 0.0

    if toil_percentage > 50:
        print(f"ALERTA: Toil representa {toil_percentage:.1f}% del tiempo (limite recomendado: 50%)")
        print("Recomendacion: priorizar iniciativas de automatizacion\n")
    else:
        print(f"Toil representa {toil_percentage:.1f}% del tiempo (dentro del limite recomendado de 50%)\n")

    return distribucion


def main():
    if len(sys.argv) != 2:
        print(f"Uso: {sys.argv[0]} <archivo.csv>")
        sys.exit(1)

    tickets = pd.read_csv(sys.argv[1])
    resultado = analizar_distribucion_trabajo(tickets)

    print("Distribucion de Trabajo:")
    print(resultado.to_string())


if __name__ == "__main__":
    main()
