#!/usr/bin/env python3
"""
Mini demo de los 3 controles tecnicos centrales del post:
  1. Cifrado selectivo de campos PII (minimizacion + proteccion en reposo).
  2. Anonimizacion de IP/user-agent mediante hash (privacy by design).
  3. Auditoria de cada acceso a datos personales (trazabilidad GDPR).

No usa Azure Key Vault ni ningun servicio externo: la clave de cifrado
se genera y guarda en un archivo local (gdpr_demo.key) para que el
ejemplo corra sin dependencias pagas. En un entorno real esa clave
viviria en un KMS/Key Vault, tal como describe el post.
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from cryptography.fernet import Fernet

KEY_FILE = Path(__file__).parent / "gdpr_demo.key"
AUDIT_LOG = Path(__file__).parent / "audit.log"

SENSITIVE_FIELDS = ["email", "phone", "address"]


def get_or_create_key() -> bytes:
    """Obtiene la clave de cifrado local o crea una nueva (simula un KMS)."""
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)
    return key


def anonymize(value: str) -> str:
    """Hashea un valor (IP, user-agent) para preservar utilidad analitica
    sin retener el dato identificable original (minimizacion de datos)."""
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def audit(action: str, subject: str, fields: list[str]) -> None:
    """Registra cada acceso a datos personales con quien/que/cuando,
    tal como exige el articulo 30 del GDPR (registro de actividades)."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "subject_id": subject,
        "fields": fields,
    }
    with AUDIT_LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")


class GDPRDataEncryption:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)

    def encrypt_personal_data(self, record: dict) -> dict:
        encrypted = dict(record)
        touched = []
        for field in SENSITIVE_FIELDS:
            if field in encrypted and encrypted[field] is not None:
                encrypted[field] = self.cipher.encrypt(
                    str(encrypted[field]).encode()
                ).decode()
                touched.append(field)

        if "ip_address" in encrypted:
            encrypted["ip_address"] = anonymize(encrypted["ip_address"])
        if "user_agent" in encrypted:
            encrypted["user_agent"] = anonymize(encrypted["user_agent"])

        encrypted["_encrypted_at"] = datetime.now(timezone.utc).isoformat()
        audit("encrypt", record.get("user_id", "unknown"), touched)
        return encrypted

    def decrypt_personal_data(self, record: dict) -> dict:
        decrypted = dict(record)
        touched = []
        for field in SENSITIVE_FIELDS:
            if field in decrypted and decrypted[field] is not None:
                decrypted[field] = self.cipher.decrypt(
                    decrypted[field].encode()
                ).decode()
                touched.append(field)

        audit("decrypt", record.get("user_id", "unknown"), touched)
        return decrypted


def main():
    # Reset del log de auditoria para que la demo sea reproducible
    if AUDIT_LOG.exists():
        AUDIT_LOG.unlink()

    key = get_or_create_key()
    engine = GDPRDataEncryption(key)

    sample_record = {
        "user_id": "user-4821",
        "email": "maria.gonzalez@example.com",
        "phone": "+34-600-123-456",
        "address": "Calle Mayor 10, Madrid, España",
        "ip_address": "203.0.113.42",
        "user_agent": "Mozilla/5.0 (X11; Linux x86_64)",
        "plan": "premium",  # dato no sensible: viaja sin cifrar
    }

    print("=== Registro original ===")
    print(json.dumps(sample_record, indent=2, ensure_ascii=False))

    encrypted = engine.encrypt_personal_data(sample_record)
    print("\n=== Registro cifrado + IP/UA anonimizados (listo para almacenar) ===")
    print(json.dumps(encrypted, indent=2, ensure_ascii=False))

    decrypted = engine.decrypt_personal_data(encrypted)
    print("\n=== Registro descifrado (acceso autorizado) ===")
    print(json.dumps(decrypted, indent=2, ensure_ascii=False))

    assert decrypted["email"] == sample_record["email"]
    assert decrypted["phone"] == sample_record["phone"]
    assert decrypted["address"] == sample_record["address"]
    assert encrypted["ip_address"] != sample_record["ip_address"]
    assert encrypted["plan"] == sample_record["plan"]  # dato no PII sin tocar

    print("\n=== Log de auditoria (audit.log) ===")
    print(AUDIT_LOG.read_text().strip())

    print("\nOK: cifrado/descifrado y anonimizacion consistentes.")


if __name__ == "__main__":
    main()
