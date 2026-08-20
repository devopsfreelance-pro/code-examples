#!/usr/bin/env python3
"""
ifc_analyzer.py - Mini motor de "Infrastructure from Code" (IfC).

Ilustra el concepto central del post: en lugar de escribir el .tf a mano,
un framework analiza estaticamente el codigo de la aplicacion (sin
ejecutarlo), detecta que recursos declara (bucket, queue, api) y genera
automaticamente la configuracion de infraestructura (aqui, Terraform/AWS).

Uso:
    python3 ifc_analyzer.py app.py

Genera generated_infra.tf con los recursos deducidos de app.py.
"""

import ast
import sys
from pathlib import Path

SDK_RESOURCE_FUNCS = {"bucket", "queue", "api"}


def analyze_call_chain(node):
    """Recorre una cadena de llamadas tipo bucket('x').allow('read','write')
    y devuelve (kind, name, permissions) o None si no es un recurso IfC."""
    permissions = []

    while isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if node.func.attr == "allow":
            permissions = [
                arg.value for arg in node.args if isinstance(arg, ast.Constant)
            ]
        node = node.func.value

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in SDK_RESOURCE_FUNCS
        and node.args
        and isinstance(node.args[0], ast.Constant)
    ):
        return node.func.id, node.args[0].value, permissions

    return None


def extract_resources(source_path: Path):
    tree = ast.parse(source_path.read_text(), filename=str(source_path))
    resources = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            found = analyze_call_chain(node.value)
            if found:
                kind, name, permissions = found
                resources.append({"kind": kind, "name": name, "permissions": permissions})

    return resources


def terraform_block(resource: dict) -> str:
    kind = resource["kind"]
    name = resource["name"]
    tf_name = name.replace("-", "_")

    if kind == "bucket":
        return (
            f'resource "aws_s3_bucket" "{tf_name}" {{\n'
            f'  bucket = "{name}"\n\n'
            f'  tags = {{\n'
            f'    ManagedBy = "ifc-analyzer"\n'
            f'  }}\n'
            f'}}\n'
        )

    if kind == "queue":
        return (
            f'resource "aws_sqs_queue" "{tf_name}" {{\n'
            f'  name = "{name}"\n\n'
            f'  tags = {{\n'
            f'    ManagedBy = "ifc-analyzer"\n'
            f'  }}\n'
            f'}}\n'
        )

    if kind == "api":
        return (
            f'resource "aws_apigatewayv2_api" "{tf_name}" {{\n'
            f'  name          = "{name}"\n'
            f'  protocol_type = "HTTP"\n\n'
            f'  tags = {{\n'
            f'    ManagedBy = "ifc-analyzer"\n'
            f'  }}\n'
            f'}}\n'
        )

    return ""


def generate_terraform(resources: list) -> str:
    header = (
        '# Generado automaticamente por ifc_analyzer.py a partir de app.py\n'
        '# NO editar a mano: los cambios de infraestructura se hacen\n'
        '# modificando el codigo de la aplicacion y re-corriendo el analizador.\n\n'
        'terraform {\n'
        '  required_providers {\n'
        '    aws = {\n'
        '      source  = "hashicorp/aws"\n'
        '      version = "~> 5.0"\n'
        '    }\n'
        '  }\n'
        '}\n\n'
        'provider "aws" {\n'
        '  region = "us-east-1"\n'
        '}\n\n'
    )
    blocks = "\n".join(terraform_block(r) for r in resources)
    return header + blocks


def main():
    if len(sys.argv) != 2:
        print("Uso: python3 ifc_analyzer.py <archivo_app.py>")
        sys.exit(1)

    source_path = Path(sys.argv[1])
    if not source_path.exists():
        print(f"No se encontro el archivo: {source_path}")
        sys.exit(1)

    resources = extract_resources(source_path)

    print(f"Analisis estatico de {source_path}:")
    print(f"{'RECURSO':<30} {'TIPO':<10} PERMISOS")
    for r in resources:
        perms = ", ".join(r["permissions"]) or "-"
        print(f"{r['name']:<30} {r['kind']:<10} {perms}")

    output_path = source_path.parent / "generated_infra.tf"
    output_path.write_text(generate_terraform(resources))

    print(f"\n{len(resources)} recursos detectados.")
    print(f"Infraestructura generada en: {output_path}")


if __name__ == "__main__":
    main()
