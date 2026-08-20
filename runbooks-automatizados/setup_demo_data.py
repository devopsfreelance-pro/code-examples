#!/usr/bin/env python3
"""
Genera datos de prueba para el runbook de ejemplo.

Crea el directorio ./demo_workspace/logs con un puñado de archivos:
- 3 archivos "viejos" (mtime forzado a 40 dias atras): deberian limpiarse.
- 2 archivos "nuevos" (mtime de hoy): NO deberian limpiarse.

Correr este script antes de ejecutar runbook_engine.py.
"""
import os
import time

WORKSPACE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_workspace")
LOGS_DIR = os.path.join(WORKSPACE, "logs")

OLD_FILES = ["app-2026-01-01.log", "app-2026-01-02.log", "worker-2026-01-01.log"]
NEW_FILES = ["app-hoy.log", "worker-hoy.log"]

FORTY_DAYS_SECONDS = 40 * 24 * 60 * 60


def main():
    os.makedirs(LOGS_DIR, exist_ok=True)

    now = time.time()
    old_timestamp = now - FORTY_DAYS_SECONDS

    for filename in OLD_FILES:
        path = os.path.join(LOGS_DIR, filename)
        with open(path, "w") as f:
            f.write(f"log de prueba (viejo): {filename}\n")
        os.utime(path, (old_timestamp, old_timestamp))

    for filename in NEW_FILES:
        path = os.path.join(LOGS_DIR, filename)
        with open(path, "w") as f:
            f.write(f"log de prueba (nuevo): {filename}\n")
        # mtime queda en "ahora" por defecto

    print(f"Datos de prueba creados en: {LOGS_DIR}")
    print(f"  Archivos viejos (>30 dias, candidatos a limpieza): {len(OLD_FILES)}")
    print(f"  Archivos nuevos (deben conservarse): {len(NEW_FILES)}")


if __name__ == "__main__":
    main()
