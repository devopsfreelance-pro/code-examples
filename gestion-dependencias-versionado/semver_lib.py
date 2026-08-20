"""
Mini-implementacion de semantic versioning y resolucion de restricciones.

Soporta los formatos de restriccion mencionados en el post:
  - Version exacta:      "1.2.3" o "==1.2.3"
  - Caret (compatible):  "^1.2.3"  -> [1.2.3, 2.0.0)
  - Tilde (solo parches): "~1.2.3" -> [1.2.3, 1.3.0)
  - Rango estilo Python:  ">=3.2,<4.0"
  - Comparadores simples: ">=2.28.1", "<4.0.0"

No usa dependencias externas: es deliberadamente simple para servir de
demo educativa, no para reemplazar `packaging` o `semver` en produccion.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    @staticmethod
    def parse(text: str) -> "Version":
        # Acepta MAJOR, MAJOR.MINOR o MAJOR.MINOR.PATCH (partes ausentes = 0),
        # como los rangos ">=3.2,<4.0" usados en requirements.txt.
        m = re.fullmatch(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", text.strip())
        if not m:
            raise ValueError(f"Version invalida: {text!r} (se espera MAJOR[.MINOR[.PATCH]])")
        major, minor, patch = m.groups()
        return Version(int(major), int(minor or 0), int(patch or 0))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


_OPS = {
    "==": lambda v, b: v == b,
    ">=": lambda v, b: v >= b,
    "<=": lambda v, b: v <= b,
    ">": lambda v, b: v > b,
    "<": lambda v, b: v < b,
}


def _caret_upper_bound(base: Version) -> Version:
    # ^1.2.3 acepta hasta la siguiente version MAJOR (o MINOR si MAJOR es 0)
    if base.major > 0:
        return Version(base.major + 1, 0, 0)
    return Version(0, base.minor + 1, 0)


def _tilde_upper_bound(base: Version) -> Version:
    # ~1.2.3 acepta solo parches: hasta la siguiente version MINOR
    return Version(base.major, base.minor + 1, 0)


def parse_constraint(text: str):
    """Devuelve una funcion Version -> bool que evalua si la version satisface la restriccion."""
    text = text.strip()

    if text.startswith("^"):
        base = Version.parse(text[1:])
        upper = _caret_upper_bound(base)
        return lambda v: base <= v < upper, f"^{base} (>= {base}, < {upper})"

    if text.startswith("~"):
        base = Version.parse(text[1:])
        upper = _tilde_upper_bound(base)
        return lambda v: base <= v < upper, f"~{base} (>= {base}, < {upper})"

    # Rango compuesto estilo Python: ">=3.2.0,<4.0.0"
    if "," in text:
        checks = []
        descriptions = []
        for part in text.split(","):
            fn, desc = parse_constraint(part.strip())
            checks.append(fn)
            descriptions.append(desc)
        return (lambda v: all(c(v) for c in checks)), " AND ".join(descriptions)

    for op, fn in sorted(_OPS.items(), key=lambda kv: -len(kv[0])):
        if text.startswith(op):
            base = Version.parse(text[len(op):])
            return (lambda v, _op=op, _base=base: _OPS[_op](v, _base)), f"{op}{base}"

    # Version exacta sin operador
    base = Version.parse(text)
    return (lambda v: v == base), f"=={base}"


def satisfies(version: str, constraint: str) -> bool:
    fn, _ = parse_constraint(constraint)
    return fn(Version.parse(version))
