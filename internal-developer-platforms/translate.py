#!/usr/bin/env python3
"""
Motor de traduccion de la plataforma interna.

Toma el spec de autoservicio (platform-spec.yaml, formato WebApplication
descrito en el post) y lo traduce a los values.yaml que consume el Helm
chart real de la plataforma (chart/). Esta es la "capa de orquestacion y
automatizacion" del post: el developer solo ve el spec simple, la
plataforma resuelve la complejidad de Kubernetes por detras.

Uso:
    python3 translate.py platform-spec.yaml > chart/values.generated.yaml
"""
import sys

import yaml


REQUIRED_FIELDS = ["image", "replicas", "resources", "port"]


def translate(spec_path: str) -> dict:
    with open(spec_path, "r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)

    if not doc or doc.get("kind") != "WebApplication":
        raise ValueError(
            f"Spec invalido: se esperaba kind: WebApplication en {spec_path}"
        )

    name = doc.get("metadata", {}).get("name")
    if not name:
        raise ValueError("Spec invalido: falta metadata.name")

    spec = doc.get("spec", {})
    missing = [field for field in REQUIRED_FIELDS if field not in spec]
    if missing:
        raise ValueError(f"Spec invalido: faltan campos spec.{missing}")

    resources = spec["resources"]

    values = {
        "name": name,
        "image": spec["image"],
        "replicas": spec["replicas"],
        "port": spec["port"],
        "resources": {
            "requests": {
                "cpu": resources["cpu"],
                "memory": resources["memory"],
            },
        },
    }
    return values


def main() -> int:
    if len(sys.argv) != 2:
        print(f"uso: {sys.argv[0]} <platform-spec.yaml>", file=sys.stderr)
        return 1

    try:
        values = translate(sys.argv[1])
    except (ValueError, FileNotFoundError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(yaml.dump(values, sort_keys=False, default_flow_style=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
