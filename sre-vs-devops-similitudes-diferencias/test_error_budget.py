#!/usr/bin/env python3
"""
Tests basicos para error_budget.py (sin dependencias externas).
Ejecutar con: python3 test_error_budget.py
"""

from error_budget import ErrorBudgetCalculator, toil_ratio


def test_allowed_downtime_99_9():
    calc = ErrorBudgetCalculator(99.9)
    # 30 dias * 24h * 60min * 0.1% = 43.2 minutos
    allowed = calc.calculate_allowed_downtime(period_hours=720)
    assert round(allowed, 1) == 43.2, f"esperado 43.2, obtenido {allowed}"


def test_budget_healthy():
    calc = ErrorBudgetCalculator(99.9)
    result = calc.remaining_budget(actual_downtime_minutes=10, period_hours=720)
    assert result["status"] == "healthy"
    assert "seguir desplegando" in result["recommendation"]


def test_budget_exhausted():
    calc = ErrorBudgetCalculator(99.9)
    result = calc.remaining_budget(actual_downtime_minutes=100, period_hours=720)
    assert result["status"] == "exhausted"
    assert "Congelar" in result["recommendation"]


def test_toil_within_target():
    result = toil_ratio(toil_hours=20, worked_hours=160)
    assert result["toil_percentage"] == 12.5
    assert "dentro del objetivo" in result["status"]


def test_toil_above_target():
    result = toil_ratio(toil_hours=100, worked_hours=160)
    assert result["toil_percentage"] == 62.5
    assert "por encima" in result["status"]


def run_all():
    tests = [
        test_allowed_downtime_99_9,
        test_budget_healthy,
        test_budget_exhausted,
        test_toil_within_target,
        test_toil_above_target,
    ]
    failures = 0
    for t in tests:
        try:
            t()
            print(f"OK   {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        raise SystemExit(f"\n{failures} test(s) fallaron")
    print("\nTodos los tests pasaron.")


if __name__ == "__main__":
    run_all()
