#!/usr/bin/env python3
"""
catalog_validator.py

Mini version del "software catalog" de Backstage.io: carga entidades
(Component, API, Resource, System) desde archivos YAML tipo catalog-info.yaml,
las indexa como lo hace el catalog-processor de Backstage y valida que las
relaciones (dependsOn / providesApis) apunten a entidades que realmente
existen en el catalogo. Tambien imprime el arbol de dependencias de cada
Component, igual que la pestaña "Dependencies" de un servicio en el portal.

Uso:
    python3 catalog_validator.py [directorio_catalogo]

Sin argumentos usa ./catalog
"""

import sys
import glob
import os
import yaml

REQUIRED_FIELDS = {
    "Component": ["type", "lifecycle", "owner"],
    "API": ["type", "lifecycle", "owner"],
    "Resource": ["type", "owner"],
}


def load_entities(catalog_dir):
    """Lee todos los YAML del directorio (soporta multiples documentos por archivo,
    como hace Backstage con los location entities) y devuelve una lista de dicts."""
    entities = []
    files = sorted(glob.glob(os.path.join(catalog_dir, "*.yaml")) +
                    glob.glob(os.path.join(catalog_dir, "*.yml")))

    if not files:
        print(f"No se encontraron archivos YAML en {catalog_dir}")
        sys.exit(1)

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            for doc in yaml.safe_load_all(f):
                if not doc:
                    continue
                doc["_source_file"] = os.path.basename(path)
                entities.append(doc)
    return entities


def entity_ref(entity):
    """Genera la referencia corta tipo 'component:default/payment-service',
    igual al formato de refs que usa Backstage internamente."""
    kind = entity.get("kind", "Unknown").lower()
    name = entity.get("metadata", {}).get("name", "sin-nombre")
    return f"{kind}:default/{name}"


def short_ref(ref):
    """Normaliza referencias como 'component:default/user-service' o
    simplemente 'user-service' a la clave usada en el indice."""
    if ":" in ref:
        return ref
    return ref


def build_index(entities):
    index = {}
    for entity in entities:
        ref = entity_ref(entity)
        index[ref] = entity
    return index


def validate_required_fields(entities):
    errors = []
    for entity in entities:
        kind = entity.get("kind")
        name = entity.get("metadata", {}).get("name", "sin-nombre")
        required = REQUIRED_FIELDS.get(kind, [])
        spec = entity.get("spec", {})
        for field in required:
            if field not in spec:
                errors.append(
                    f"[{entity['_source_file']}] {kind} '{name}': falta 'spec.{field}'"
                )
    return errors


def validate_relations(entities, index):
    """Verifica que dependsOn y providesApis apunten a entidades existentes.
    Esto es lo que en Backstage real dispara un 'processing error' visible
    en la UI del catalogo cuando una relacion queda rota."""
    errors = []
    for entity in entities:
        name = entity.get("metadata", {}).get("name", "sin-nombre")
        spec = entity.get("spec", {})

        for ref in spec.get("dependsOn", []):
            if ref not in index:
                errors.append(
                    f"[{entity['_source_file']}] '{name}' depende de "
                    f"'{ref}', pero esa entidad no existe en el catalogo"
                )

        for api_name in spec.get("providesApis", []):
            api_ref = f"api:default/{api_name}"
            if api_ref not in index:
                errors.append(
                    f"[{entity['_source_file']}] '{name}' provee la API "
                    f"'{api_name}', pero no hay ningun API con ese nombre"
                )
    return errors


def print_catalog_summary(entities):
    print("Software Catalog\n" + "=" * 40)
    by_kind = {}
    for entity in entities:
        kind = entity.get("kind", "Unknown")
        by_kind.setdefault(kind, []).append(entity)

    for kind in sorted(by_kind):
        print(f"\n{kind} ({len(by_kind[kind])})")
        for entity in by_kind[kind]:
            meta = entity.get("metadata", {})
            spec = entity.get("spec", {})
            owner = spec.get("owner", "-")
            print(f"  - {meta.get('name')}  (owner={owner})")


def print_dependency_tree(entities, index):
    print("\nArbol de dependencias\n" + "=" * 40)
    components = [e for e in entities if e.get("kind") == "Component"]
    for component in components:
        name = component["metadata"]["name"]
        print(f"\n{name}")
        deps = component.get("spec", {}).get("dependsOn", [])
        if not deps:
            print("  (sin dependencias)")
        for dep in deps:
            status = "OK" if dep in index else "ROTA"
            print(f"  -> {dep}  [{status}]")


def main():
    catalog_dir = sys.argv[1] if len(sys.argv) > 1 else "catalog"

    entities = load_entities(catalog_dir)
    index = build_index(entities)

    print_catalog_summary(entities)
    print_dependency_tree(entities, index)

    print("\nValidacion\n" + "=" * 40)
    errors = validate_required_fields(entities) + validate_relations(entities, index)

    if not errors:
        print("Catalogo valido: todas las entidades y relaciones son correctas.")
        sys.exit(0)

    print(f"{len(errors)} problema(s) encontrado(s):\n")
    for error in errors:
        print(f"  x {error}")
    sys.exit(1)


if __name__ == "__main__":
    main()
