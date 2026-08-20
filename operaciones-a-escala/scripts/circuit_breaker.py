#!/usr/bin/env python3
"""
Mini implementacion de Circuit Breaker (patron de resiliencia mencionado
en el post) para ilustrar como un sistema a escala evita cascading
failures cuando una dependencia empieza a fallar.

No requiere dependencias externas. Simula una llamada a un servicio
downstream que falla intermitentemente y muestra como el circuit breaker
pasa de CLOSED -> OPEN -> HALF_OPEN -> CLOSED.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from enum import Enum


class State(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class CircuitBreaker:
    max_failures: int = 3
    reset_timeout: float = 5.0
    failures: int = 0
    state: State = State.CLOSED
    last_failure_time: float = field(default=0.0)

    def call(self, fn):
        if self.state is State.OPEN:
            if time.monotonic() - self.last_failure_time > self.reset_timeout:
                self.state = State.HALF_OPEN
                self.failures = 0
            else:
                raise RuntimeError("circuit breaker abierto: llamada rechazada")

        try:
            result = fn()
        except Exception:
            self.failures += 1
            self.last_failure_time = time.monotonic()
            if self.failures >= self.max_failures:
                self.state = State.OPEN
            raise

        # Exito: si estabamos probando en half-open, cerramos el circuito
        self.failures = 0
        self.state = State.CLOSED
        return result


def unreliable_downstream_call(failure_rate: float = 0.6) -> str:
    if random.random() < failure_rate:
        raise ConnectionError("downstream service timeout")
    return "200 OK"


def main() -> None:
    breaker = CircuitBreaker(max_failures=3, reset_timeout=3.0)

    for attempt in range(1, 21):
        try:
            response = breaker.call(lambda: unreliable_downstream_call(0.6))
            print(f"[{attempt:02d}] estado={breaker.state.value:9s} -> exito: {response}")
        except RuntimeError as e:
            print(f"[{attempt:02d}] estado={breaker.state.value:9s} -> rechazado: {e}")
        except ConnectionError as e:
            print(f"[{attempt:02d}] estado={breaker.state.value:9s} -> fallo: {e}")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
