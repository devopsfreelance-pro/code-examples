#!/usr/bin/env python3
"""
Calculadora de las 4 DORA metrics a partir de un archivo JSON con
despliegues e incidentes.

Uso:
    python3 dora_metrics.py deployments.json
"""
import json
import sys
from datetime import datetime, timedelta

FMT = "%Y-%m-%dT%H:%M:%S"


def parse(ts: str) -> datetime:
    return datetime.strptime(ts, FMT)


def cargar_datos(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------
# 1. Frecuencia de despliegue
# ---------------------------------------------------------------------
def categorizar_frecuencia(frecuencia_diaria: float) -> str:
    if frecuencia_diaria >= 1:
        return "Elite"
    elif frecuencia_diaria >= 0.14:  # al menos semanal
        return "Alto"
    elif frecuencia_diaria >= 0.033:  # al menos mensual
        return "Medio"
    return "Bajo"


def calcular_frecuencia_despliegue(despliegues: list, periodo_dias: int) -> dict:
    fechas = [parse(d["deployed_at"]) for d in despliegues]
    fecha_fin = max(fechas)
    fecha_inicio = fecha_fin - timedelta(days=periodo_dias)

    despliegues_periodo = [f for f in fechas if fecha_inicio <= f <= fecha_fin]
    frecuencia = len(despliegues_periodo) / periodo_dias

    return {
        "despliegues_totales": len(despliegues_periodo),
        "periodo_dias": periodo_dias,
        "frecuencia_diaria": round(frecuencia, 2),
        "categoria": categorizar_frecuencia(frecuencia),
    }


# ---------------------------------------------------------------------
# 2. Tiempo de entrega de cambios (Lead Time for Changes)
# ---------------------------------------------------------------------
def categorizar_lead_time(horas_promedio: float) -> str:
    if horas_promedio < 24:
        return "Elite"
    elif horas_promedio < 24 * 7:
        return "Alto"
    elif horas_promedio < 24 * 30:
        return "Medio"
    return "Bajo"


def calcular_lead_time(despliegues: list) -> dict:
    horas = [
        (parse(d["deployed_at"]) - parse(d["commit_created_at"])).total_seconds() / 3600
        for d in despliegues
    ]
    promedio = sum(horas) / len(horas)

    return {
        "lead_time_promedio_horas": round(promedio, 2),
        "lead_time_maximo_horas": round(max(horas), 2),
        "categoria": categorizar_lead_time(promedio),
    }


# ---------------------------------------------------------------------
# 3. Tiempo medio de recuperación (MTTR)
# ---------------------------------------------------------------------
def categorizar_mttr(minutos_promedio: float) -> str:
    if minutos_promedio < 60:
        return "Elite"
    elif minutos_promedio < 24 * 60:
        return "Alto"
    elif minutos_promedio < 7 * 24 * 60:
        return "Medio"
    return "Bajo"


def calcular_mttr(incidentes: list) -> dict:
    if not incidentes:
        return {"mttr_promedio_minutos": 0, "incidentes_totales": 0, "categoria": "Elite"}

    minutos = [
        (parse(i["resolved_at"]) - parse(i["detected_at"])).total_seconds() / 60
        for i in incidentes
    ]
    promedio = sum(minutos) / len(minutos)

    return {
        "mttr_promedio_minutos": round(promedio, 1),
        "incidentes_totales": len(incidentes),
        "categoria": categorizar_mttr(promedio),
    }


# ---------------------------------------------------------------------
# 4. Tasa de fallos en cambios (Change Failure Rate)
# ---------------------------------------------------------------------
def categorizar_cfr(tasa_pct: float) -> str:
    if tasa_pct <= 15:
        return "Elite/Alto"
    elif tasa_pct <= 46:
        return "Medio"
    return "Bajo"


def calcular_change_failure_rate(despliegues: list, incidentes: list) -> dict:
    total_despliegues = len(despliegues)

    despliegues_fallidos = {
        i["deployment_id"] for i in incidentes if i.get("deployment_id")
    }

    tasa = len(despliegues_fallidos) / total_despliegues if total_despliegues else 0

    return {
        "tasa_fallos_pct": round(tasa * 100, 1),
        "despliegues_totales": total_despliegues,
        "despliegues_fallidos": len(despliegues_fallidos),
        "categoria": categorizar_cfr(tasa * 100),
    }


def main():
    if len(sys.argv) != 2:
        print("Uso: python3 dora_metrics.py deployments.json")
        sys.exit(1)

    datos = cargar_datos(sys.argv[1])
    despliegues = datos["despliegues"]
    incidentes = datos["incidentes"]

    # periodo_dias = ventana entre el primer y el ultimo despliegue del dataset
    fechas = [parse(d["deployed_at"]) for d in despliegues]
    periodo_dias = max((max(fechas) - min(fechas)).days, 1)

    resultado = {
        "1_frecuencia_despliegue": calcular_frecuencia_despliegue(despliegues, periodo_dias),
        "2_lead_time_for_changes": calcular_lead_time(despliegues),
        "3_mean_time_to_recovery": calcular_mttr(incidentes),
        "4_change_failure_rate": calcular_change_failure_rate(despliegues, incidentes),
    }

    print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
