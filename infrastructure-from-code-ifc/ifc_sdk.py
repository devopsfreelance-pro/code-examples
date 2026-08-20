"""
ifc_sdk.py - SDK didactico minimo al estilo Nitric/Klotho/Ampt.

Esta NO es una libreria real de infraestructura: los recursos declarados
aqui no se aprovisionan solos. Su unico proposito es que el codigo de
aplicacion (ver app.py) pueda "declarar" recursos de forma parecida a como
lo hacen los frameworks reales de Infrastructure from Code, para que
ifc_analyzer.py pueda leerlos por analisis estatico y generar la
infraestructura equivalente (ver el ejemplo de Nitric en el post).
"""

from dataclasses import dataclass, field


@dataclass
class Resource:
    kind: str
    name: str
    permissions: list = field(default_factory=list)

    def allow(self, *permissions):
        self.permissions.extend(permissions)
        return self


def bucket(name: str) -> Resource:
    """Declara un bucket de almacenamiento de objetos (ej: S3)."""
    return Resource(kind="bucket", name=name)


def queue(name: str) -> Resource:
    """Declara una cola de mensajes (ej: SQS)."""
    return Resource(kind="queue", name=name)


def api(name: str) -> Resource:
    """Declara una API HTTP (ej: API Gateway)."""
    return Resource(kind="api", name=name)
