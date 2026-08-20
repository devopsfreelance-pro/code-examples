"""
Compara full sync vs checkpoint sync sobre la cadena generada por
generate_chain.py y mide el tiempo y la cantidad de bloques que cada
estrategia tiene que verificar con "expensive_state_check" (el trabajo
costoso que en un nodo real seria re-ejecutar transacciones para
reconstruir el estado).

Uso:
    python3 generate_chain.py
    python3 sync_demo.py
"""

import json
import time

from chain_lib import (
    GENESIS_HASH,
    expensive_state_check,
    load_chain,
    verify_link,
)

WORK_ITERATIONS = 20000  # costo simulado de validar el estado de 1 bloque
DIFFICULTY_PREFIX = "0"


def full_sync(chain):
    """Sincroniza desde el bloque genesis: verifica el enlace y el
    estado de TODOS los bloques, en orden."""
    start = time.perf_counter()
    prev_hash = GENESIS_HASH
    verified = 0
    for block in chain:
        if not verify_link(block, prev_hash, DIFFICULTY_PREFIX):
            raise ValueError(f"Cadena invalida en el bloque {block.index}")
        if not expensive_state_check(block, WORK_ITERATIONS):
            raise ValueError(f"Estado invalido en el bloque {block.index}")
        prev_hash = block.hash
        verified += 1
    elapsed = time.perf_counter() - start
    return elapsed, verified


def checkpoint_sync(chain, checkpoint):
    """Sincroniza confiando en un checkpoint: solo verifica que el
    checkpoint coincida con el bloque correspondiente en la cadena
    (en un nodo real esto se compara contra weak subjectivity /
    varios pares), y luego hace el trabajo costoso unicamente para
    los bloques posteriores al checkpoint."""
    start = time.perf_counter()

    checkpoint_block = chain[checkpoint["index"]]
    if checkpoint_block.hash != checkpoint["hash"]:
        raise ValueError("El checkpoint no coincide con la cadena: no es confiable")
    if checkpoint_block.prev_hash != checkpoint["prev_hash"]:
        raise ValueError("El checkpoint tiene un prev_hash inconsistente")

    # Los bloques 0..checkpoint quedan "confiados" sin re-ejecutar su estado.
    prev_hash = checkpoint_block.hash
    verified = 1  # el propio checkpoint

    for block in chain[checkpoint["index"] + 1:]:
        if not verify_link(block, prev_hash, DIFFICULTY_PREFIX):
            raise ValueError(f"Cadena invalida en el bloque {block.index}")
        if not expensive_state_check(block, WORK_ITERATIONS):
            raise ValueError(f"Estado invalido en el bloque {block.index}")
        prev_hash = block.hash
        verified += 1

    elapsed = time.perf_counter() - start
    return elapsed, verified


def main() -> None:
    chain = load_chain("chain.json")
    with open("checkpoint.json", "r", encoding="utf-8") as f:
        checkpoint = json.load(f)

    print(f"Cadena cargada: {len(chain)} bloques. Checkpoint en bloque #{checkpoint['index']}.\n")

    full_time, full_verified = full_sync(chain)
    print(f"[full sync]       bloques verificados: {full_verified:5d}  tiempo: {full_time:.2f}s")

    ckpt_time, ckpt_verified = checkpoint_sync(chain, checkpoint)
    print(f"[checkpoint sync] bloques verificados: {ckpt_verified:5d}  tiempo: {ckpt_time:.2f}s")

    speedup = full_time / ckpt_time if ckpt_time > 0 else float("inf")
    print(f"\nCheckpoint sync fue {speedup:.1f}x mas rapido que full sync")
    print(
        f"y solo tuvo que re-ejecutar el estado de {ckpt_verified} bloques "
        f"en vez de los {full_verified} bloques completos del historial."
    )


if __name__ == "__main__":
    main()
