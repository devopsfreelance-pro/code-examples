#!/usr/bin/env python3
"""
Mini resolvedor de dependencias.

Simula lo que hace un gestor de paquetes (npm, pip, Maven) al instalar:
1. Lee el manifiesto (requires directos con restricciones semver).
2. Resuelve cada dependencia directa a la version mas alta disponible que
   cumple la restriccion.
3. Recolecta las dependencias TRANSITIVAS de cada una y detecta si dos
   paquetes distintos exigen restricciones incompatibles de una misma
   dependencia compartida ("dependency hell", ver seccion del post).
4. Si la resolucion es exitosa, escribe un lockfile (`lock.json`) con las
   versiones exactas elegidas, igual que package-lock.json o poetry.lock.

Uso:
    python3 resolve_dependencies.py dependencies.json
    python3 resolve_dependencies.py dependencies-fixed.json --lockfile lock.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from semver_lib import Version, parse_constraint

HERE = Path(__file__).parent


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def highest_satisfying(available: list[str], constraints: list[str]) -> str | None:
    """Devuelve la version mas alta en `available` que cumple TODAS las constraints."""
    checks = [parse_constraint(c)[0] for c in constraints]
    candidates = [
        v for v in available
        if all(check(Version.parse(v)) for check in checks)
    ]
    if not candidates:
        return None
    return str(max(Version.parse(v) for v in candidates))


def resolve(manifest: dict, registry: dict) -> tuple[dict, list[str]]:
    resolved: dict[str, str] = {}
    conflicts: list[str] = []

    # Paso 1: dependencias directas del proyecto
    for pkg, constraint in manifest["requires"].items():
        available = list(registry[pkg].keys())
        chosen = highest_satisfying(available, [constraint])
        if chosen is None:
            conflicts.append(
                f"No hay version de '{pkg}' que satisfaga la restriccion directa "
                f"'{constraint}'. Disponibles: {available}"
            )
            continue
        resolved[pkg] = chosen

    # Paso 2: agrupar restricciones transitivas por paquete compartido
    transitive_constraints: dict[str, list[tuple[str, str]]] = {}
    for pkg, version in resolved.items():
        transitive = registry[pkg][version]
        for dep_name, dep_constraint in transitive.items():
            transitive_constraints.setdefault(dep_name, []).append((pkg, dep_constraint))

    # Paso 3: resolver cada dependencia transitiva compartida
    for dep_name, requirers in transitive_constraints.items():
        available = list(registry[dep_name].keys())
        constraints = [c for _, c in requirers]
        chosen = highest_satisfying(available, constraints)
        if chosen is None:
            detail = ", ".join(f"{who} exige '{c}'" for who, c in requirers)
            conflicts.append(
                f"CONFLICTO en '{dep_name}': {detail}. "
                f"Ninguna version disponible ({available}) satisface todas las "
                f"restricciones simultaneamente. Esto es 'dependency hell'."
            )
            continue
        resolved[dep_name] = chosen

    return resolved, conflicts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="Archivo de manifiesto (ej: dependencies.json)")
    parser.add_argument(
        "--registry", default=str(HERE / "registry.json"),
        help="Archivo con las versiones disponibles de cada paquete (default: registry.json)",
    )
    parser.add_argument(
        "--lockfile", default=None,
        help="Si se indica, escribe el resultado en este archivo (ej: lock.json)",
    )
    args = parser.parse_args()

    manifest = load_json(Path(args.manifest))
    registry = load_json(Path(args.registry))

    print(f"Resolviendo dependencias para '{manifest['project']}'...\n")
    for pkg, constraint in manifest["requires"].items():
        print(f"  requiere directo: {pkg} {constraint}")
    print()

    resolved, conflicts = resolve(manifest, registry)

    if conflicts:
        print("RESOLUCION FALLIDA\n")
        for c in conflicts:
            print(f"  - {c}")
        print(
            "\nAsi se ve un conflicto real de versiones: dos dependencias "
            "necesitan rangos incompatibles de una misma libreria compartida. "
            "La solucion (segun el post) es actualizar una de las dependencias "
            "principales a una version que relaje el rango, o usar un mecanismo "
            "de resolucion forzada (ej. 'overrides' en npm)."
        )
        return 1

    print("RESOLUCION EXITOSA\n")
    for pkg, version in sorted(resolved.items()):
        origin = "directa" if pkg in manifest["requires"] else "transitiva"
        print(f"  {pkg} -> {version}  ({origin})")

    if args.lockfile:
        lock = {
            "project": manifest["project"],
            "resolved": dict(sorted(resolved.items())),
        }
        with open(args.lockfile, "w", encoding="utf-8") as f:
            json.dump(lock, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"\nLockfile escrito en '{args.lockfile}'.")
        print(
            "Corre este comando de nuevo: el resultado sera identico byte a byte, "
            "porque el registry y el manifiesto no cambiaron. Esa es la garantia "
            "de reproducibilidad que da un lockfile (package-lock.json, poetry.lock, etc)."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
