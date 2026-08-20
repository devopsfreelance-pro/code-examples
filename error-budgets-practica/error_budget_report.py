#!/usr/bin/env python3
"""
Calculadora de Error Budget con gate de despliegue.

Simula 30 dias de trafico horario para un servicio (con seed fija, asi que
la salida es siempre la misma), calcula cuanto error budget queda respecto
a un SLO objetivo, evalua el burn rate (multi-ventana, estilo Google SRE:
1h y 6h) y decide si un despliegue puede proceder, igual que el
`ErrorBudgetGate` descripto en el post.

Sin dependencias externas: solo libreria estandar de Python 3.
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass


@dataclass
class HourBucket:
    hour_index: int
    total_requests: int
    error_requests: int

    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.error_requests / self.total_requests


def generate_synthetic_traffic(hours: int = 24 * 30, seed: int = 42) -> list[HourBucket]:
    """Genera trafico horario sintetico con una tasa de error de base
    (~0.06%) y dos incidentes inyectados para que el ejemplo sea realista:
    un pico corto (1h) y un incidente sostenido (6h) hacia el final,
    que es lo que dispara las alertas de burn rate."""
    rng = random.Random(seed)
    buckets: list[HourBucket] = []

    for hour in range(hours):
        base_requests = rng.randint(8_000, 12_000)
        base_error_rate = rng.uniform(0.0002, 0.0008)  # ruido normal

        # Incidente corto y agudo: hora 500, burn rate muy alto en ventana de 1h
        if hour == 500:
            base_error_rate = 0.05

        # Incidente sostenido: horas 700-705 (6h), burn rate moderado pero prolongado
        if 700 <= hour < 706:
            base_error_rate = 0.012

        errors = int(base_requests * base_error_rate)
        buckets.append(HourBucket(hour_index=hour, total_requests=base_requests, error_requests=errors))

    return buckets


class ErrorBudgetGate:
    """Replica la logica del post: SLO objetivo, ventana de evaluacion,
    umbral minimo de budget para desplegar y deteccion de burn rate."""

    def __init__(self, slo_target: float = 0.999, window_hours: int = 24 * 30, min_budget_to_deploy: float = 0.20):
        self.slo_target = slo_target
        self.window_hours = window_hours
        self.min_budget_to_deploy = min_budget_to_deploy
        self.allowed_error_rate = 1 - slo_target

    def remaining_budget(self, buckets: list[HourBucket]) -> float:
        window = buckets[-self.window_hours:]
        total_requests = sum(b.total_requests for b in window)
        total_errors = sum(b.error_requests for b in window)
        if total_requests == 0:
            return 1.0
        current_error_rate = total_errors / total_requests
        consumed = current_error_rate / self.allowed_error_rate
        return max(0.0, 1 - consumed)

    def burn_rate(self, buckets: list[HourBucket], window_hours: int) -> float:
        """Burn rate = (tasa de error observada) / (tasa de error permitida
        por el SLO). 1.0 significa 'quemando budget al ritmo exacto del
        presupuesto mensual'; 14.4x agotaria el budget mensual en ~2 dias."""
        window = buckets[-window_hours:]
        total_requests = sum(b.total_requests for b in window)
        total_errors = sum(b.error_requests for b in window)
        if total_requests == 0:
            return 0.0
        observed_error_rate = total_errors / total_requests
        return observed_error_rate / self.allowed_error_rate

    def can_proceed_with_deployment(self, buckets: list[HourBucket]) -> dict:
        remaining = self.remaining_budget(buckets)
        burn_1h = self.burn_rate(buckets, window_hours=1)
        burn_6h = self.burn_rate(buckets, window_hours=6)

        if remaining < self.min_budget_to_deploy:
            return {
                "allowed": False,
                "reason": f"Error budget insuficiente: {remaining * 100:.1f}% restante (minimo {self.min_budget_to_deploy * 100:.0f}%)",
                "remaining_budget": remaining,
                "burn_rate_1h": burn_1h,
                "burn_rate_6h": burn_6h,
            }

        # Umbrales estandar de Google SRE workbook: 14.4x en 1h o 6x en 6h
        if burn_1h > 14.4:
            return {
                "allowed": False,
                "reason": f"Burn rate critico en ventana de 1h: {burn_1h:.1f}x (umbral 14.4x)",
                "remaining_budget": remaining,
                "burn_rate_1h": burn_1h,
                "burn_rate_6h": burn_6h,
            }

        if burn_6h > 6.0:
            return {
                "allowed": False,
                "reason": f"Burn rate elevado y sostenido en ventana de 6h: {burn_6h:.1f}x (umbral 6.0x)",
                "remaining_budget": remaining,
                "burn_rate_1h": burn_1h,
                "burn_rate_6h": burn_6h,
            }

        return {
            "allowed": True,
            "reason": "Budget suficiente y burn rate dentro de rango normal",
            "remaining_budget": remaining,
            "burn_rate_1h": burn_1h,
            "burn_rate_6h": burn_6h,
        }


def print_report(buckets: list[HourBucket], gate: ErrorBudgetGate) -> dict:
    total_requests = sum(b.total_requests for b in buckets)
    total_errors = sum(b.error_requests for b in buckets)
    overall_error_rate = total_errors / total_requests

    decision = gate.can_proceed_with_deployment(buckets)

    print("=" * 60)
    print("REPORTE DE ERROR BUDGET")
    print("=" * 60)
    print(f"SLO objetivo:              {gate.slo_target * 100:.2f}%")
    print(f"Ventana evaluada:          {len(buckets)} horas ({len(buckets) / 24:.0f} dias)")
    print(f"Requests totales:          {total_requests:,}")
    print(f"Errores totales:           {total_errors:,}")
    print(f"Tasa de error observada:   {overall_error_rate * 100:.4f}%")
    print(f"Tasa de error permitida:   {gate.allowed_error_rate * 100:.4f}%")
    print("-" * 60)
    print(f"Error budget restante:     {decision['remaining_budget'] * 100:.1f}%")
    print(f"Burn rate (ventana 1h):    {decision['burn_rate_1h']:.2f}x")
    print(f"Burn rate (ventana 6h):    {decision['burn_rate_6h']:.2f}x")
    print("-" * 60)
    estado = "PERMITIDO" if decision["allowed"] else "BLOQUEADO"
    print(f"Despliegue:                {estado}")
    print(f"Motivo:                    {decision['reason']}")
    print("=" * 60)

    return decision


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculadora de error budget con gate de despliegue")
    parser.add_argument("--slo", type=float, default=0.999, help="SLO objetivo, ej: 0.999 para 99.9%%")
    parser.add_argument("--hours", type=int, default=24 * 30, help="Horas de trafico sintetico a simular")
    parser.add_argument("--seed", type=int, default=42, help="Seed del generador de trafico sintetico")
    parser.add_argument("--min-budget", type=float, default=0.20, help="Budget minimo requerido para desplegar")
    args = parser.parse_args()

    buckets = generate_synthetic_traffic(hours=args.hours, seed=args.seed)
    gate = ErrorBudgetGate(slo_target=args.slo, window_hours=args.hours, min_budget_to_deploy=args.min_budget)
    decision = print_report(buckets, gate)

    return 0 if decision["allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
