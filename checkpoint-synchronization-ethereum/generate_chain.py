"""
Genera una cadena de bloques de juguete y un checkpoint "confiable"
en un punto avanzado de esa cadena, tal como lo publicaria un
proveedor de checkpoints (checkpointz, servicios de la Beacon Chain,
etc.) para que los clientes hagan checkpoint sync.

Uso:
    python3 generate_chain.py
"""

import json

from chain_lib import build_chain, save_chain, GENESIS_HASH

CHAIN_LENGTH = 1500
CHECKPOINT_INDEX = 1400  # ultimos 100 bloques quedan "sin checkpointear"
DIFFICULTY_PREFIX = "0"  # bajo para que la generacion sea rapida


def main() -> None:
    print(f"Generando cadena de {CHAIN_LENGTH} bloques (puede tardar unos segundos)...")
    chain = build_chain(CHAIN_LENGTH, difficulty_prefix=DIFFICULTY_PREFIX)
    save_chain(chain, "chain.json")

    checkpoint_block = chain[CHECKPOINT_INDEX]
    checkpoint = {
        "index": checkpoint_block.index,
        "hash": checkpoint_block.hash,
        "prev_hash": checkpoint_block.prev_hash,
        "note": (
            "Checkpoint finalizado y distribuido por un proveedor confiable. "
            "Un cliente en modo checkpoint sync arranca aca en vez de en el "
            "bloque genesis."
        ),
    }
    with open("checkpoint.json", "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)

    print(f"Cadena guardada en chain.json ({len(chain)} bloques).")
    print(f"Checkpoint guardado en checkpoint.json (bloque #{CHECKPOINT_INDEX}).")
    print(f"Bloque genesis esperado: {GENESIS_HASH}")


if __name__ == "__main__":
    main()
