#!/usr/bin/env python3
"""
affected.py - Version minima de "nx affected" para el ejemplo del post
Monorepo vs Multirepo.

Lee un grafo de dependencias (dependency-graph.json), calcula que archivos
cambiaron respecto a un commit base con `git diff`, determina que proyectos
fueron tocados directamente y expande el resultado a los proyectos que
dependen de ellos (transitivamente). Solo esos proyectos "afectados" se
"prueban" (se simula con un echo), tal como haria un pipeline de CI real
con Nx/Turborepo en un monorepo.

Uso:
    python3 affected.py --repo <path> --base <git-ref> --graph <graph.json>
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def get_changed_files(repo: Path, base_ref: str) -> list[str]:
    output = run_git(repo, "diff", "--name-only", base_ref, "HEAD")
    return [line.strip() for line in output.splitlines() if line.strip()]


def load_graph(graph_path: Path) -> dict:
    with graph_path.open() as fh:
        return json.load(fh)


def directly_changed_projects(changed_files: list[str], projects: dict) -> set[str]:
    changed = set()
    for name, meta in projects.items():
        prefix = meta["path"].rstrip("/") + "/"
        for f in changed_files:
            if f.startswith(prefix):
                changed.add(name)
                break
    return changed


def expand_with_dependents(seed: set[str], projects: dict) -> set[str]:
    """Agrega cualquier proyecto que dependa (directa o transitivamente)
    de alguno de los proyectos en `seed`."""
    affected = set(seed)
    changed_in_pass = True
    while changed_in_pass:
        changed_in_pass = False
        for name, meta in projects.items():
            if name in affected:
                continue
            deps = set(meta.get("dependsOn", []))
            if deps & affected:
                affected.add(name)
                changed_in_pass = True
    return affected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="Path al repo del monorepo demo")
    parser.add_argument("--base", required=True, help="Ref git base para comparar (ej: HEAD~1)")
    parser.add_argument("--graph", required=True, help="Path a dependency-graph.json")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    graph_path = Path(args.graph).resolve()

    graph = load_graph(graph_path)
    projects = graph["projects"]

    changed_files = get_changed_files(repo, args.base)
    if not changed_files:
        print("No hay archivos modificados respecto a la base indicada.")
        return 0

    print(f"Archivos modificados desde {args.base}:")
    for f in changed_files:
        print(f"  - {f}")

    seed = directly_changed_projects(changed_files, projects)
    affected = expand_with_dependents(seed, projects)

    all_projects = set(projects.keys())
    skipped = all_projects - affected

    print(f"\nProyectos tocados directamente: {sorted(seed) or '(ninguno)'}")
    print(f"Proyectos afectados (directos + dependientes): {sorted(affected) or '(ninguno)'}")
    print(f"Proyectos NO afectados (se saltan build/test): {sorted(skipped) or '(ninguno)'}")

    print("\nEjecutando pipeline solo sobre proyectos afectados:")
    for name in sorted(affected):
        print(f"  -> nx run {name}:test   [OK] (simulado)")
        print(f"  -> nx run {name}:build  [OK] (simulado)")

    if skipped:
        print("\nProyectos saltados (sin cambios relevantes, ahorran tiempo de CI):")
        for name in sorted(skipped):
            print(f"  -> {name}: skip")

    return 0


if __name__ == "__main__":
    sys.exit(main())
