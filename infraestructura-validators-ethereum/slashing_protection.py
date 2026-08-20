#!/usr/bin/env python3
"""
slashing_protection.py

Implementacion pedagogica y simplificada de una base de "slashing protection"
en formato EIP-3076 (el mismo formato que exportan/importan clientes reales
como Lighthouse, Teku o Prysm con `slashing-protection export/import`).

Objetivo del ejemplo: mostrar en codigo la regla operativa del post
"un juego de llaves de validador vive en un solo lugar" -- que pasa si,
por accidente (nodo de respaldo, migracion mal hecha), se intenta firmar
dos veces con la misma llave.

NO es un reemplazo del cliente slashing-protection DB real (esa logica vive
en Lighthouse/Teku y tiene mas casos borde). Sirve para entender el
mecanismo: doble voto, voto envolvente (surrounding vote) y doble propuesta
de bloque, y por que aceptar downtime es mejor que arriesgar un failover.
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ValidatorRecord:
    pubkey: str
    min_source_epoch: Optional[int] = None
    max_source_epoch: Optional[int] = None
    min_target_epoch: Optional[int] = None
    max_target_epoch: Optional[int] = None
    max_slot: Optional[int] = None
    # signing_root por (source, target) y por slot, para permitir reintentos
    # idempotentes (volver a firmar EXACTAMENTE lo mismo no es slashing).
    attestation_roots: Dict[str, str] = field(default_factory=dict)
    block_roots: Dict[str, str] = field(default_factory=dict)


class SlashingProtectionDB:
    """DB en memoria construida a partir de un interchange file EIP-3076."""

    def __init__(self):
        self.validators: Dict[str, ValidatorRecord] = {}

    @classmethod
    def load(cls, path: str) -> "SlashingProtectionDB":
        with open(path, "r", encoding="utf-8") as f:
            interchange = json.load(f)

        db = cls()
        for entry in interchange.get("data", []):
            pubkey = entry["pubkey"]
            record = ValidatorRecord(pubkey=pubkey)

            for att in entry.get("signed_attestations", []):
                source = int(att["source_epoch"])
                target = int(att["target_epoch"])
                root = att.get("signing_root", "")

                record.min_source_epoch = (
                    source if record.min_source_epoch is None
                    else min(record.min_source_epoch, source)
                )
                record.max_source_epoch = (
                    source if record.max_source_epoch is None
                    else max(record.max_source_epoch, source)
                )
                record.min_target_epoch = (
                    target if record.min_target_epoch is None
                    else min(record.min_target_epoch, target)
                )
                record.max_target_epoch = (
                    target if record.max_target_epoch is None
                    else max(record.max_target_epoch, target)
                )
                record.attestation_roots[f"{source}:{target}"] = root

            for blk in entry.get("signed_blocks", []):
                slot = int(blk["slot"])
                root = blk.get("signing_root", "")
                record.max_slot = (
                    slot if record.max_slot is None else max(record.max_slot, slot)
                )
                record.block_roots[str(slot)] = root

            db.validators[pubkey] = record

        return db

    def check_attestation(
        self, pubkey: str, source_epoch: int, target_epoch: int, signing_root: str
    ):
        """Devuelve (permitido: bool, motivo: str)."""
        record = self.validators.get(pubkey)
        if record is None or record.max_target_epoch is None:
            return True, "primera attestation registrada para esta llave"

        key = f"{source_epoch}:{target_epoch}"
        if key in record.attestation_roots:
            if record.attestation_roots[key] == signing_root:
                return True, "reintento idempotente (mismo voto ya firmado)"
            return False, (
                "DOBLE VOTO: mismo source/target ya firmado con un signing_root "
                "distinto (dos procesos firmando la misma llave)"
            )

        if target_epoch <= record.max_target_epoch:
            return False, (
                f"DOBLE VOTO: target_epoch {target_epoch} <= max_target_epoch ya "
                f"firmado ({record.max_target_epoch})"
            )

        if (
            source_epoch < record.min_source_epoch
            and target_epoch > record.max_target_epoch
        ):
            return False, (
                "VOTO ENVOLVENTE (surrounding vote): esta attestation envuelve "
                "un voto anterior"
            )

        if source_epoch < record.max_source_epoch:
            return False, (
                "VOTO ENVUELTO (surrounded vote): source_epoch anterior a un "
                "source ya usado con target mayor"
            )

        return True, "attestation valida, no viola reglas de slashing"

    def check_block(self, pubkey: str, slot: int, signing_root: str):
        record = self.validators.get(pubkey)
        if record is None or record.max_slot is None:
            return True, "primer bloque registrado para esta llave"

        key = str(slot)
        if key in record.block_roots:
            if record.block_roots[key] == signing_root:
                return True, "reintento idempotente (mismo bloque ya firmado)"
            return False, (
                "DOBLE PROPUESTA: mismo slot ya firmado con un signing_root "
                "distinto (dos procesos firmando la misma llave)"
            )

        if slot <= record.max_slot:
            return False, (
                f"DOBLE PROPUESTA: slot {slot} <= max_slot ya firmado "
                f"({record.max_slot})"
            )

        return True, "bloque valido, no viola reglas de slashing"

    def record_attestation(self, pubkey: str, source_epoch: int, target_epoch: int, signing_root: str):
        record = self.validators.setdefault(pubkey, ValidatorRecord(pubkey=pubkey))
        record.min_source_epoch = (
            source_epoch if record.min_source_epoch is None
            else min(record.min_source_epoch, source_epoch)
        )
        record.max_source_epoch = (
            source_epoch if record.max_source_epoch is None
            else max(record.max_source_epoch, source_epoch)
        )
        record.min_target_epoch = (
            target_epoch if record.min_target_epoch is None
            else min(record.min_target_epoch, target_epoch)
        )
        record.max_target_epoch = (
            target_epoch if record.max_target_epoch is None
            else max(record.max_target_epoch, target_epoch)
        )
        record.attestation_roots[f"{source_epoch}:{target_epoch}"] = signing_root

    def record_block(self, pubkey: str, slot: int, signing_root: str):
        record = self.validators.setdefault(pubkey, ValidatorRecord(pubkey=pubkey))
        record.max_slot = slot if record.max_slot is None else max(record.max_slot, slot)
        record.block_roots[str(slot)] = signing_root


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Simulador pedagogico de slashing protection (formato EIP-3076). "
            "Verifica si firmar una nueva attestation o bloque violaria las "
            "reglas de doble voto / doble propuesta antes de dejarlo pasar."
        )
    )
    parser.add_argument("db_path", help="Ruta al interchange file EIP-3076 (JSON)")
    sub = parser.add_subparsers(dest="action", required=True)

    att = sub.add_parser("check-attestation", help="Verificar una attestation nueva")
    att.add_argument("--pubkey", required=True)
    att.add_argument("--source-epoch", type=int, required=True)
    att.add_argument("--target-epoch", type=int, required=True)
    att.add_argument("--signing-root", required=True)

    blk = sub.add_parser("check-block", help="Verificar una propuesta de bloque nueva")
    blk.add_argument("--pubkey", required=True)
    blk.add_argument("--slot", type=int, required=True)
    blk.add_argument("--signing-root", required=True)

    args = parser.parse_args()
    db = SlashingProtectionDB.load(args.db_path)

    if args.action == "check-attestation":
        allowed, reason = db.check_attestation(
            args.pubkey, args.source_epoch, args.target_epoch, args.signing_root
        )
    else:
        allowed, reason = db.check_block(args.pubkey, args.slot, args.signing_root)

    status = "PERMITIDO" if allowed else "BLOQUEADO"
    print(f"[{status}] {reason}")
    sys.exit(0 if allowed else 1)


if __name__ == "__main__":
    main()
