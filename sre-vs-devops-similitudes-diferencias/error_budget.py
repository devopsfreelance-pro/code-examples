#!/usr/bin/env python3
"""
Calculadora de Error Budget y Toil (SRE).

Demuestra la diferencia central entre DevOps y SRE que describe el post:
DevOps no prescribe una forma de medir confiabilidad, mientras que SRE
la cuantifica con SLOs, Error Budgets y el porcentaje de toil.

Uso:
    python3 error_budget.py --slo 99.9 --period-hours 720 --downtime-minutes 30 --toil-hours 20 --worked-hours 160
"""

import argparse
import sys


class ErrorBudgetCalculator:
    def __init__(self, slo_percentage: float):
        if not 0 < slo_percentage < 100:
            raise ValueError("slo_percentage debe estar entre 0 y 100")
        self.slo = slo_percentage
        self.error_budget_pct = 100 - slo_percentage

    def calculate_allowed_downtime(self, period_hours: float) -> float:
        """Minutos de downtime permitidos en el periodo segun el SLO."""
        total_minutes = period_hours * 60
        return total_minutes * (self.error_budget_pct / 100)

    def remaining_budget(self, actual_downtime_minutes: float, period_hours: float) -> dict:
        """Presupuesto de error restante tras un downtime real."""
        allowed = self.calculate_allowed_downtime(period_hours)
        remaining = allowed - actual_downtime_minutes
        percentage = (remaining / allowed) * 100 if allowed > 0 else 0
        return {
            "allowed_downtime_minutes": round(allowed, 2),
            "actual_downtime_minutes": actual_downtime_minutes,
            "remaining_minutes": round(remaining, 2),
            "remaining_percentage": round(percentage, 2),
            "status": "healthy" if remaining >= 0 else "exhausted",
            # Politica de error budget: guía la decisión de "seguir lanzando"
            # vs "congelar features y enfocarse en confiabilidad".
            "recommendation": (
                "OK para seguir desplegando nuevas features"
                if remaining >= 0
                else "Congelar features nuevas y priorizar confiabilidad"
            ),
        }


def toil_ratio(toil_hours: float, worked_hours: float) -> dict:
    """SRE recomienda mantener el toil por debajo del 50% del tiempo del equipo."""
    if worked_hours <= 0:
        raise ValueError("worked_hours debe ser mayor a 0")
    pct = (toil_hours / worked_hours) * 100
    return {
        "toil_hours": toil_hours,
        "worked_hours": worked_hours,
        "toil_percentage": round(pct, 2),
        "status": "dentro del objetivo (<50%)" if pct < 50 else "por encima del objetivo SRE (>=50%)",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Calculadora de Error Budget y Toil al estilo SRE."
    )
    parser.add_argument("--slo", type=float, required=True, help="SLO objetivo en porcentaje, ej: 99.9")
    parser.add_argument("--period-hours", type=float, required=True, help="Duracion del periodo a evaluar, en horas")
    parser.add_argument("--downtime-minutes", type=float, required=True, help="Downtime real ocurrido en el periodo, en minutos")
    parser.add_argument("--toil-hours", type=float, default=None, help="Horas dedicadas a toil en el periodo (opcional)")
    parser.add_argument("--worked-hours", type=float, default=None, help="Horas totales trabajadas por el equipo en el periodo (opcional)")
    args = parser.parse_args()

    calculator = ErrorBudgetCalculator(slo_percentage=args.slo)
    result = calculator.remaining_budget(
        actual_downtime_minutes=args.downtime_minutes,
        period_hours=args.period_hours,
    )

    print("=== Error Budget ===")
    print(f"SLO objetivo:            {args.slo}%")
    print(f"Downtime permitido:      {result['allowed_downtime_minutes']} min")
    print(f"Downtime real:           {result['actual_downtime_minutes']} min")
    print(f"Presupuesto restante:    {result['remaining_minutes']} min ({result['remaining_percentage']}%)")
    print(f"Estado:                  {result['status']}")
    print(f"Recomendacion:           {result['recommendation']}")

    if args.toil_hours is not None and args.worked_hours is not None:
        toil = toil_ratio(args.toil_hours, args.worked_hours)
        print("\n=== Toil ===")
        print(f"Horas de toil:           {toil['toil_hours']}")
        print(f"Horas trabajadas:        {toil['worked_hours']}")
        print(f"Porcentaje de toil:      {toil['toil_percentage']}%")
        print(f"Estado:                  {toil['status']}")
    elif args.toil_hours is not None or args.worked_hours is not None:
        print(
            "\nAviso: para calcular toil hay que pasar --toil-hours y --worked-hours juntos.",
            file=sys.stderr,
        )

    sys.exit(0 if result["status"] == "healthy" else 1)


if __name__ == "__main__":
    main()
