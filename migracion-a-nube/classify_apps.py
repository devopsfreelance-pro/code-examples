#!/usr/bin/env python3
"""classify_apps.py

Simula la fase de "Evaluacion y Planificacion" del post: toma un inventario
de aplicaciones on-premise, las clasifica segun el marco de las 6 R
(Rehost, Replatform, Refactor, Repurchase, Retire, Retain) y agrupa el
resultado en oleadas (waves) de migracion.

Para que el ejemplo sea ejecutable sin cuenta de AWS, cada app del
inventario se registra como una instancia EC2 (con tags) en LocalStack.
Esto reemplaza a AWS Application Discovery Service (que no es gratis ni
esta disponible en LocalStack Community) manteniendo la misma idea: cada
aplicacion queda como un recurso con metadata que despues se consulta y
se agrupa.

Uso:
    python3 classify_apps.py
"""

import sys

import boto3

LOCALSTACK_ENDPOINT = "http://localhost:4566"

# Inventario de aplicaciones on-premise a evaluar. En un caso real esto
# saldria de una herramienta de discovery; aca lo hardcodeamos para que el
# ejemplo sea reproducible.
APP_INVENTORY = [
    {"name": "web-frontend-legacy", "criticality": "high", "complexity": "low", "age_years": 2},
    {"name": "billing-mainframe-batch", "criticality": "high", "complexity": "high", "age_years": 15},
    {"name": "internal-crm-custom", "criticality": "medium", "complexity": "high", "age_years": 8},
    {"name": "reporting-cronjobs", "criticality": "low", "complexity": "high", "age_years": 10},
    {"name": "auth-service", "criticality": "high", "complexity": "medium", "age_years": 3},
    {"name": "old-intranet-portal", "criticality": "low", "complexity": "low", "age_years": 12},
]

# AMI de ejemplo: LocalStack Community no valida que exista de verdad,
# solo necesita un formato de ID plausible.
FAKE_AMI_ID = "ami-0c55b159cbfafe1f0"


def classify_strategy(app: dict) -> str:
    """Aplica reglas simples inspiradas en el marco de las 6 R del post."""
    criticality = app["criticality"]
    complexity = app["complexity"]
    age = app["age_years"]

    if criticality == "low" and complexity == "high":
        return "retire"
    if criticality == "low" and age >= 10:
        return "retain"
    if app["name"].endswith("crm-custom"):
        return "repurchase"
    if criticality == "high" and complexity == "high":
        return "refactor"
    if complexity == "medium":
        return "replatform"
    return "rehost"


# Cada estrategia cae en una oleada de ejecucion: primero se sacan del
# alcance las que no requieren migrar infraestructura (retire/retain),
# despues las rapidas (rehost), luego las que llevan trabajo moderado
# (replatform/repurchase) y al final las que requieren re-arquitectura
# (refactor).
STRATEGY_WAVE = {
    "retire": 1,
    "retain": 1,
    "rehost": 2,
    "replatform": 3,
    "repurchase": 3,
    "refactor": 4,
}


def register_inventory(ec2_client, apps_with_strategy: list) -> None:
    """Registra cada app como una instancia EC2 tagueada en LocalStack."""
    for app in apps_with_strategy:
        ec2_client.run_instances(
            ImageId=FAKE_AMI_ID,
            InstanceType="t3.micro",
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Name", "Value": app["name"]},
                        {"Key": "MigrationStrategy", "Value": app["strategy"]},
                        {"Key": "Criticality", "Value": app["criticality"]},
                        {"Key": "Wave", "Value": str(app["wave"])},
                    ],
                }
            ],
        )


def print_report(apps_with_strategy: list) -> None:
    waves = {}
    for app in apps_with_strategy:
        waves.setdefault(app["wave"], []).append(app)

    print("Plan de migracion por oleadas (6R)")
    print("=" * 40)
    for wave in sorted(waves):
        print(f"\nOleada {wave}:")
        for app in waves[wave]:
            print(
                f"  - {app['name']:<28} strategy={app['strategy']:<11} "
                f"criticality={app['criticality']:<6} age={app['age_years']}y"
            )


def main() -> int:
    apps_with_strategy = []
    for app in APP_INVENTORY:
        strategy = classify_strategy(app)
        wave = STRATEGY_WAVE[strategy]
        apps_with_strategy.append({**app, "strategy": strategy, "wave": wave})

    try:
        ec2 = boto3.client(
            "ec2",
            region_name="us-east-1",
            endpoint_url=LOCALSTACK_ENDPOINT,
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )
        register_inventory(ec2, apps_with_strategy)
    except Exception as exc:  # noqa: BLE001 - se reporta y se sigue con el reporte local
        print(f"Aviso: no se pudo registrar el inventario en LocalStack ({exc}).", file=sys.stderr)
        print("Verifica que 'docker compose up -d' este corriendo. Continuo solo con el reporte.\n", file=sys.stderr)

    print_report(apps_with_strategy)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
