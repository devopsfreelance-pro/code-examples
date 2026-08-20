"""
Catalogo de plantillas y reglas de gobernanza del sistema de autoservicio.

Representa, en forma minima, las dos capas que describe el post:

- Capa de abstraccion/orquestacion: TEMPLATES traduce nombres de alto nivel
  ("nodejs-microservice") en configuraciones concretas de infraestructura
  (imagen base, puerto, motor de base de datos, etc).
- Capa de control y gobernanza: GOVERNANCE_RULES valida que la solicitud
  cumpla politicas organizacionales (tamanos de compute permitidos por
  ambiente, bases de datos aprobadas) antes de que se aprovisione nada.
"""

from __future__ import annotations

# Plantillas disponibles en el catalogo de autoservicio.
TEMPLATES = {
    "nodejs-microservice": {
        "base_image": "node:20-alpine",
        "container_port": 3000,
        "health_check_path": "/healthz",
    },
    "python-api": {
        "base_image": "python:3.12-slim",
        "container_port": 8000,
        "health_check_path": "/health",
    },
}

# Motores de base de datos aprobados por el catalogo.
DATABASES = {
    "postgres-dev": {"engine": "postgres", "version": "16", "tier": "shared"},
    "postgres-prod": {"engine": "postgres", "version": "16", "tier": "dedicated"},
}

# Tamanos de compute permitidos por ambiente (guardrail de costos).
ALLOWED_COMPUTE_BY_ENV = {
    "development": {"small", "medium"},
    "staging": {"small", "medium", "large"},
    "production": {"medium", "large", "xlarge"},
}

COMPUTE_SPECS = {
    "small": {"cpu": "250m", "memory": "512Mi"},
    "medium": {"cpu": "500m", "memory": "1Gi"},
    "large": {"cpu": "1", "memory": "2Gi"},
    "xlarge": {"cpu": "2", "memory": "4Gi"},
}


class GovernanceViolation(Exception):
    """Se levanta cuando una ServiceRequest viola una politica organizacional."""


def validate_request(spec: dict) -> None:
    """Aplica las reglas de gobernanza. Levanta GovernanceViolation si falla."""
    template = spec.get("template")
    if template not in TEMPLATES:
        raise GovernanceViolation(
            f"template '{template}' no existe en el catalogo. "
            f"Opciones: {sorted(TEMPLATES)}"
        )

    environment = spec.get("environment")
    if environment not in ALLOWED_COMPUTE_BY_ENV:
        raise GovernanceViolation(
            f"environment '{environment}' no es valido. "
            f"Opciones: {sorted(ALLOWED_COMPUTE_BY_ENV)}"
        )

    resources = spec.get("resources", {})
    compute = resources.get("compute")
    allowed = ALLOWED_COMPUTE_BY_ENV[environment]
    if compute not in allowed:
        raise GovernanceViolation(
            f"compute '{compute}' no esta permitido en environment "
            f"'{environment}'. Permitidos: {sorted(allowed)}"
        )

    database = resources.get("database")
    if database not in DATABASES:
        raise GovernanceViolation(
            f"database '{database}' no existe en el catalogo. "
            f"Opciones: {sorted(DATABASES)}"
        )

    if not spec.get("gitRepository"):
        raise GovernanceViolation("gitRepository es obligatorio (trazabilidad).")

    if not spec.get("owner"):
        raise GovernanceViolation("owner es obligatorio (trazabilidad/costos).")
