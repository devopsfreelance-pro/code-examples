#!/usr/bin/env python3
"""
Mini motor de runbooks automatizados.

Ilustra el concepto central del post "Que es un Runbook: Guia Practica":
un runbook automatizado convierte pasos manuales en codigo ejecutable, con
pre-validaciones, pasos idempotentes, manejo de errores, post-validaciones,
logging estructurado y notificacion, sin intervencion humana.

Uso:
    python3 runbook_engine.py runbooks/cleanup-old-logs.yaml --dry-run
    python3 runbook_engine.py runbooks/cleanup-old-logs.yaml
"""
import argparse
import json
import os
import sys
import time

try:
    import yaml
except ImportError:
    print("Falta pyyaml. Instalar con: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runbook.log.jsonl")


def log_event(event: dict) -> None:
    """Logging estructurado en JSON Lines, como recomienda el post."""
    event["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(f"[{event.get('status', 'info').upper()}] {event.get('step', event.get('phase'))}: "
          f"{event.get('message', '')}")


def notify(channel: str, message: str) -> None:
    """Notificacion al equipo. En este demo, consola; en produccion seria
    Slack, email o un sistema de tickets."""
    print(f"[NOTIFY:{channel}] {message}")


# --- Registro de acciones disponibles para el runbook -----------------

def check_directory_exists(params: dict) -> tuple:
    target_dir = _resolve_path(params["target_dir"])
    if not os.path.isdir(target_dir):
        return False, f"El directorio {target_dir} no existe"
    return True, f"Directorio {target_dir} verificado"


def count_old_files(params: dict, dry_run: bool) -> dict:
    old_files = _find_old_files(params)
    return {"old_file_count": len(old_files), "files": old_files}


def delete_old_files(params: dict, dry_run: bool) -> dict:
    old_files = _find_old_files(params)
    deleted = []
    for path in old_files:
        if dry_run:
            deleted.append(path)
        else:
            os.remove(path)
            deleted.append(path)
    action = "simulados (dry-run)" if dry_run else "eliminados"
    return {"deleted_count": len(deleted), "files": deleted, "action": action}


def verify_cleanup(params: dict, dry_run: bool) -> dict:
    if dry_run:
        # En dry-run no se elimino nada de verdad, asi que no verificamos estado real.
        return {"skipped": True, "reason": "dry-run: no se modifico el filesystem"}
    remaining = _find_old_files(params)
    if remaining:
        raise RuntimeError(f"Quedan {len(remaining)} archivos viejos sin eliminar: {remaining}")
    return {"remaining_old_files": 0}


ACTIONS = {
    "count_old_files": count_old_files,
    "delete_old_files": delete_old_files,
    "verify_cleanup": verify_cleanup,
}

PRE_VALIDATIONS = {
    "check_directory_exists": check_directory_exists,
}


# --- Helpers -----------------------------------------------------------

def _resolve_path(path: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return path if os.path.isabs(path) else os.path.join(base_dir, path)


def _find_old_files(params: dict) -> list:
    target_dir = _resolve_path(params["target_dir"])
    max_age_days = params["max_age_days"]
    cutoff = time.time() - (max_age_days * 24 * 60 * 60)

    old_files = []
    if not os.path.isdir(target_dir):
        return old_files

    for filename in sorted(os.listdir(target_dir)):
        path = os.path.join(target_dir, filename)
        if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
            old_files.append(path)
    return old_files


# --- Motor de ejecucion --------------------------------------------------

def run_runbook(runbook_path: str, dry_run: bool) -> int:
    with open(runbook_path) as f:
        runbook = yaml.safe_load(f)

    metadata = runbook["metadata"]
    params = runbook["params"]
    channel = runbook.get("notifications", {}).get("channel", "console")

    log_event({
        "phase": "start",
        "status": "info",
        "message": f"Iniciando runbook '{metadata['name']}' (dry_run={dry_run})",
    })

    # Pre-validaciones: si alguna falla, se aborta sin ejecutar nada.
    for check_name in runbook.get("pre_validations", []):
        check_fn = PRE_VALIDATIONS[check_name]
        ok, message = check_fn(params)
        if not ok:
            log_event({"phase": "pre_validation", "step": check_name, "status": "error", "message": message})
            notify(channel, runbook["notifications"].get("on_failure", "Runbook fallido"))
            return 1
        log_event({"phase": "pre_validation", "step": check_name, "status": "ok", "message": message})

    # Pasos principales, en orden, con manejo de errores.
    for step in runbook.get("steps", []):
        action_fn = ACTIONS[step["action"]]
        try:
            result = action_fn(params, dry_run)
            log_event({
                "phase": "step", "step": step["name"], "status": "ok",
                "message": step.get("description", ""), "result": result,
            })
        except Exception as exc:  # manejo de errores: abortar y notificar
            log_event({"phase": "step", "step": step["name"], "status": "error", "message": str(exc)})
            notify(channel, runbook["notifications"].get("on_failure", "Runbook fallido"))
            return 1

    # Post-validaciones: confirman el estado deseado tras ejecutar los pasos.
    for post_check in runbook.get("post_validations", []):
        action_fn = ACTIONS[post_check["action"]]
        try:
            result = action_fn(params, dry_run)
            log_event({
                "phase": "post_validation", "step": post_check["name"], "status": "ok",
                "message": post_check.get("description", ""), "result": result,
            })
        except Exception as exc:
            log_event({"phase": "post_validation", "step": post_check["name"], "status": "error", "message": str(exc)})
            notify(channel, runbook["notifications"].get("on_failure", "Runbook fallido"))
            return 1

    notify(channel, runbook["notifications"].get("on_success", "Runbook completado"))
    log_event({"phase": "end", "status": "ok", "message": "Runbook finalizado con exito"})
    return 0


def main():
    parser = argparse.ArgumentParser(description="Motor de runbooks automatizados (demo)")
    parser.add_argument("runbook", help="Ruta al archivo YAML del runbook")
    parser.add_argument("--dry-run", action="store_true", help="Simula la ejecucion sin modificar el filesystem")
    args = parser.parse_args()

    exit_code = run_runbook(args.runbook, args.dry_run)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
