"""
Libreria minima para simular una cadena de bloques y el costo de
verificacion de estado (state transition) que hace un cliente Ethereum
al sincronizar.

No es una implementacion real de Ethereum: es un modelo simplificado
que reproduce la idea central de checkpoint synchronization:

  - full sync: verifica el estado desde el bloque genesis (indice 0)
    hasta la cabeza de la cadena, bloque por bloque.
  - checkpoint sync: confia en un checkpoint (finalizado y firmado por
    la red / distribuido por un proveedor de checkpoints) y solo
    verifica el estado de los bloques posteriores a ese checkpoint.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from typing import List


GENESIS_HASH = "0" * 64


def _block_hash(index: int, prev_hash: str, data: str, nonce: int) -> str:
    payload = f"{index}:{prev_hash}:{data}:{nonce}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass
class Block:
    index: int
    prev_hash: str
    data: str
    nonce: int
    hash: str

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Block":
        return Block(**d)


def mine_block(index: int, prev_hash: str, data: str, difficulty_prefix: str = "00") -> Block:
    """Encuentra un nonce tal que el hash del bloque empiece con
    'difficulty_prefix'. Simula el trabajo de sellar un bloque
    (en Ethereum PoS esto seria la firma/atestacion del validador).
    """
    nonce = 0
    while True:
        h = _block_hash(index, prev_hash, data, nonce)
        if h.startswith(difficulty_prefix):
            return Block(index=index, prev_hash=prev_hash, data=data, nonce=nonce, hash=h)
        nonce += 1


def build_chain(length: int, difficulty_prefix: str = "00") -> List[Block]:
    chain: List[Block] = []
    prev_hash = GENESIS_HASH
    for i in range(length):
        block = mine_block(i, prev_hash, data=f"tx-batch-{i}", difficulty_prefix=difficulty_prefix)
        chain.append(block)
        prev_hash = block.hash
    return chain


def save_chain(chain: List[Block], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([b.to_dict() for b in chain], f, indent=2)


def load_chain(path: str) -> List[Block]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Block.from_dict(b) for b in raw]


def expensive_state_check(block: Block, work_iterations: int = 20000) -> bool:
    """Simula el costo de re-ejecutar las transacciones de un bloque
    para reconstruir su estado (lo que geth hace en full sync para
    cada bloque del historial). El resultado no se usa mas alla de
    forzar el trabajo de CPU: lo que importa es el tiempo que toma.
    """
    digest = block.hash.encode("utf-8")
    for _ in range(work_iterations):
        digest = hashlib.sha256(digest).digest()
    return len(digest) == 32


def verify_link(block: Block, prev_hash: str, difficulty_prefix: str = "00") -> bool:
    """Verifica que el hash del bloque sea consistente con su contenido
    y que encadene correctamente con el bloque anterior."""
    if block.prev_hash != prev_hash:
        return False
    recomputed = _block_hash(block.index, block.prev_hash, block.data, block.nonce)
    if recomputed != block.hash:
        return False
    return block.hash.startswith(difficulty_prefix)
