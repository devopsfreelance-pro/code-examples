#!/usr/bin/env python3
"""
scaffold.py - Mini Internal Developer Platform (IDP) scaffolder.

Simula el "golden path" que ofrece una plataforma tipo Backstage: un developer
pide un servicio nuevo con un solo comando y recibe la estructura completa
(Dockerfile, CI/CD, manifests de Kubernetes, monitoreo y registro en catálogo)
lista para usar, en vez de armarla a mano.

Uso:
    python3 scaffold.py --name mi-servicio --database postgresql --cache redis
    python3 scaffold.py --name mi-servicio   # sin database ni cache

No requiere dependencias externas (solo stdlib).
"""

import argparse
import re
import sys
from pathlib import Path
from string import Template

TEMPLATES_DIR = Path(__file__).parent / "templates"
VALID_DATABASES = {"none", "postgresql", "mongodb", "dynamodb"}
VALID_CACHES = {"none", "redis", "memcached"}
NAME_PATTERN = re.compile(r"^[a-z0-9-]+$")


def validate_name(name: str) -> None:
    if not NAME_PATTERN.match(name):
        raise ValueError(
            f"Nombre de servicio invalido: '{name}'. "
            "Debe cumplir el patron '^[a-z0-9-]+$' (minusculas, numeros, guiones)."
        )


def render_template(template_name: str, context: dict) -> str:
    template_path = TEMPLATES_DIR / template_name
    content = template_path.read_text(encoding="utf-8")
    return Template(content).safe_substitute(context)


def write_file(base_dir: Path, relative_path: str, content: str) -> None:
    target = base_dir / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    print(f"  creado  {target.relative_to(base_dir.parent)}")


def scaffold_service(name: str, owner: str, database: str, cache: str, output_root: Path) -> Path:
    validate_name(name)
    if database not in VALID_DATABASES:
        raise ValueError(f"database invalida: {database}. Opciones: {sorted(VALID_DATABASES)}")
    if cache not in VALID_CACHES:
        raise ValueError(f"cache invalida: {cache}. Opciones: {sorted(VALID_CACHES)}")

    service_dir = output_root / name
    if service_dir.exists():
        raise FileExistsError(f"El directorio '{service_dir}' ya existe. Elegi otro --name.")

    context = {
        "service_name": name,
        "owner": owner,
        "database": database,
        "cache": cache,
        "needs_database": "true" if database != "none" else "false",
        "needs_cache": "true" if cache != "none" else "false",
    }

    print(f"Generando servicio '{name}' (owner={owner}, database={database}, cache={cache})\n")

    mapping = {
        "Dockerfile.tmpl": "Dockerfile",
        "ci-cd.yaml.tmpl": ".github/workflows/ci-cd.yaml",
        "deployment.yaml.tmpl": "k8s/deployment.yaml",
        "service.yaml.tmpl": "k8s/service.yaml",
        "ingress.yaml.tmpl": "k8s/ingress.yaml",
        "hpa.yaml.tmpl": "k8s/hpa.yaml",
        "alerts.yaml.tmpl": "monitoring/alerts.yaml",
        "catalog-info.yaml.tmpl": "catalog-info.yaml",
        "index.md.tmpl": "docs/index.md",
    }

    for template_name, relative_path in mapping.items():
        rendered = render_template(template_name, context)
        write_file(service_dir, relative_path, rendered)

    (service_dir / "src").mkdir(parents=True, exist_ok=True)
    (service_dir / "src" / ".gitkeep").write_text("", encoding="utf-8")
    print(f"  creado  {(service_dir / 'src').relative_to(output_root)}/ (codigo de la app va aca)")

    return service_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Golden path: genera un microservicio con CI/CD, K8s, monitoreo y catalogo."
    )
    parser.add_argument("--name", required=True, help="Nombre del servicio, ej: orders-api")
    parser.add_argument("--owner", default="platform-team", help="Equipo owner (default: platform-team)")
    parser.add_argument(
        "--database", default="none", choices=sorted(VALID_DATABASES), help="Base de datos a provisionar"
    )
    parser.add_argument("--cache", default="none", choices=sorted(VALID_CACHES), help="Cache a provisionar")
    parser.add_argument(
        "--output", default=".", help="Directorio donde crear el servicio (default: directorio actual)"
    )
    args = parser.parse_args()

    output_root = Path(args.output).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    try:
        service_dir = scaffold_service(args.name, args.owner, args.database, args.cache, output_root)
    except (ValueError, FileExistsError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"\nListo. Servicio '{args.name}' generado en: {service_dir}")
    print("Proximos pasos: 'cd', inicializar git, hacer push y dejar que CI/CD tome el resto.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
