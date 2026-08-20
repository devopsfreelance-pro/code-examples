"""
Exporter Prometheus para métricas tipo blockchain.

Simula un nodo Ethereum (número de bloque, precio de gas, transacciones
pendientes) para que el ejemplo funcione sin depender de un proveedor de
nodos pago (Infura/Alchemy) ni de una API key. La lógica de exposición de
métricas (Gauge + start_http_server) es la misma que usarías conectando
un cliente real de web3.py contra un nodo Ethereum, tal como se explica
en el post del blog.
"""
import random
import time

from prometheus_client import Gauge, start_http_server

# Métricas Prometheus (mismos nombres que en el post)
block_number = Gauge("ethereum_block_number", "Número de bloque actual")
gas_price = Gauge("ethereum_gas_price_gwei", "Precio de gas en Gwei")
pending_transactions = Gauge("ethereum_pending_tx", "Transacciones pendientes")

# Estado inicial simulado
_current_block = 21_000_000


def simulate_node_read():
    """Simula una lectura de nodo blockchain (block_number, gas_price, pending_tx).

    En un exporter real esto sería:
        current_block = w3.eth.block_number
        current_gas = w3.eth.gas_price / 10**9
        pending_tx = len(w3.eth.get_block('pending')['transactions'])
    """
    global _current_block
    _current_block += random.randint(0, 2)
    current_gas = round(random.uniform(8, 120), 2)
    pending_tx = random.randint(50, 5000)
    return _current_block, current_gas, pending_tx


def collect_metrics():
    while True:
        try:
            current_block, current_gas, pending_tx = simulate_node_read()

            block_number.set(current_block)
            gas_price.set(current_gas)
            pending_transactions.set(pending_tx)

            print(
                f"block={current_block} gas={current_gas}gwei "
                f"pending_tx={pending_tx}"
            )
        except Exception as e:
            print(f"Error recolectando métricas: {e}")

        time.sleep(5)


if __name__ == "__main__":
    start_http_server(8000)  # Exponer métricas en http://localhost:8000/metrics
    collect_metrics()
