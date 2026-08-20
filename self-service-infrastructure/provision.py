#!/usr/bin/env python3
"""
Orquestador minimo del "infrastructure portal" descripto en el post.

Flujo (las mismas 4 capas que describe el articulo):

  1. Portal:      lee una ServiceRequest declarativa (YAML) del desarrollador.
  2. Gobernanza:  valida la solicitud contra el catalogo y las politicas
                  organizacionales (catalog.py) ANTES de tocar infraestructura.
  3. Orquestacion: traduce la solicitud validada a variables de Terraform.
  4. Infraestructura: corre Terraform, que "aprovisiona" el entorno
                  (localmente, con el provider `local`, sin nube real).

Uso:
    python3 provision.py service-request.yaml
    python3 provision.py service-request-invalid.yaml   # rechazado
"""

import json
import subprocess
import sys
from pathlib import Path

import yaml

from catalog import (
    COMPUTE_SPECS,
    DATABASES,
    TEMPLATES,
    GovernanceViolation,
    validate_request,
)

TFVARS_PATH = Path(__file__).parent / "terraform.tfvars.json"


def load_request(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        doc = yaml.safe_load(f)

    if doc.get("kind") != "ServiceRequest":
        raise ValueError(f"kind '{doc.get('kind')}' no es 'ServiceRequest'")

    return doc


def build_tfvars(doc: dict) -> dict:
    spec = doc["spec"]
    template = TEMPLATES[spec["template"]]
    database = DATABASES[spec["resources"]["database"]]
    compute = COMPUTE_SPECS[spec["resources"]["compute"]]

    return {
        "service_name": doc["metadata"]["name"],
        "environment": spec["environment"],
        "owner": spec["owner"],
        "git_repository": spec["gitRepository"],
        "base_image": template["base_image"],
        "container_port": template["container_port"],
        "health_check_path": template["health_check_path"],
        "db_engine": database["engine"],
        "db_version": database["version"],
        "db_tier": database["tier"],
        "compute_cpu": compute["cpu"],
        "compute_memory": compute["memory"],
        "integrations": spec.get("integrations", []),
    }


def run_terraform() -> None:
    subprocess.run(["terraform", "init", "-input=false"], check=True)
    subprocess.run(
        ["terraform", "apply", "-auto-approve", "-input=false"], check=True
    )


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Uso: {sys.argv[0]} <service-request.yaml>", file=sys.stderr)
        return 2

    request_path = sys.argv[1]

    print(f"[portal] leyendo solicitud: {request_path}")
    doc = load_request(request_path)
    spec = doc["spec"]

    print(f"[gobernanza] validando '{doc['metadata']['name']}' contra el catalogo...")
    try:
        validate_request(spec)
    except GovernanceViolation as exc:
        print(f"[gobernanza] SOLICITUD RECHAZADA: {exc}", file=sys.stderr)
        return 1
    print("[gobernanza] solicitud aprobada.")

    print("[orquestacion] generando variables de Terraform...")
    tfvars = build_tfvars(doc)
    TFVARS_PATH.write_text(json.dumps(tfvars, indent=2), encoding="utf-8")
    print(f"[orquestacion] escrito {TFVARS_PATH.name}")

    print("[infraestructura] aprovisionando con Terraform...")
    run_terraform()

    print("\nListo. Entorno provisionado. Ver environment-manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
