#!/usr/bin/env python3
"""Corre las mismas herramientas que el pipeline del post (pylint,
radon, pytest --cov) contra sample_app/calculator.py y agrega el
resultado a metrics_history.json.

Uso:
    python3 scripts/collect_metrics.py <etiqueta-de-la-iteracion>

Equivale a los pasos "Analisis de codigo estatico", "Metricas de
complejidad" y "Cobertura de pruebas" del pipeline YAML del post,
mas el paso "Publicar metricas a dashboard" (aqui, un JSON local en
vez de un dashboard real).
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HISTORY_FILE = ROOT / "metrics_history.json"


def run_pylint() -> int:
    """Devuelve la cantidad de issues que reporta pylint (0 = codigo limpio)."""
    proc = subprocess.run(
        ["pylint", "sample_app/calculator.py", "--output-format=json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    try:
        issues = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        issues = []
    return len(issues)


def run_radon_complexity() -> float:
    """Devuelve la complejidad ciclomatica promedio de calculator.py."""
    proc = subprocess.run(
        ["radon", "cc", "sample_app/calculator.py", "-j"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    data = json.loads(proc.stdout or "{}")
    blocks = next(iter(data.values()), [])
    if not blocks:
        return 0.0
    total = sum(block["complexity"] for block in blocks)
    return round(total / len(blocks), 2)


def run_coverage() -> float:
    """Devuelve el porcentaje de cobertura de tests sobre calculator.py."""
    subprocess.run(
        [
            "pytest",
            "--cov=sample_app",
            "--cov-report=json",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    coverage_file = ROOT / "coverage.json"
    if not coverage_file.exists():
        return 0.0
    data = json.loads(coverage_file.read_text())
    return round(data["totals"]["percent_covered"], 1)


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python3 scripts/collect_metrics.py <etiqueta>")
        sys.exit(1)
    label = sys.argv[1]

    entry = {
        "label": label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pylint_issues": run_pylint(),
        "complexity_avg": run_radon_complexity(),
        "coverage_pct": run_coverage(),
    }

    history = []
    if HISTORY_FILE.exists():
        history = json.loads(HISTORY_FILE.read_text())
    history.append(entry)
    HISTORY_FILE.write_text(json.dumps(history, indent=2))

    print(
        f"[{label}] pylint_issues={entry['pylint_issues']} "
        f"complexity_avg={entry['complexity_avg']} "
        f"coverage_pct={entry['coverage_pct']}%"
    )


if __name__ == "__main__":
    main()
