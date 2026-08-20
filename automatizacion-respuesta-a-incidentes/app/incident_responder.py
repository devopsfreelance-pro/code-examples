"""
Motor mínimo de automatización de respuesta a incidentes.

Recibe alertas estilo Alertmanager (POST /webhook/alert), las clasifica,
ejecuta un runbook de mitigación y aplica las prácticas del post:
- Modo dry-run (solo notifica, no ejecuta).
- Idempotencia (no repite la misma acción si el incidente ya fue mitigado).
- Límite duro / circuit breaker (máximo N acciones por alerta por hora).
- Logging estructurado de cada decisión y resultado.
- Escalamiento a on-call cuando la automatización no puede resolver.
"""
import json
import logging
import os
import sys
import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from flask import Flask, jsonify, request

app = Flask(__name__)

DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"
MAX_ACTIONS_PER_HOUR = int(os.environ.get("MAX_ACTIONS_PER_HOUR", "3"))
WINDOW_SECONDS = 3600

# Estado en memoria (en producción: Redis/DB). Suficiente para el demo.
action_history = defaultdict(deque)  # alertname -> deque[timestamp]
resolved_incidents = set()  # alertnames ya mitigados y aún "firing" (idempotencia)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("incident-responder")


def log_event(**fields):
    """Logging estructurado en JSON, una línea por evento (fácil de auditar)."""
    event = {"timestamp": datetime.now(timezone.utc).isoformat()}
    event.update(fields)
    logger.info(json.dumps(event, ensure_ascii=False))


def classify(alert):
    """Clasifica severidad y decide si el alertname tiene runbook conocido."""
    labels = alert.get("labels", {})
    severity = labels.get("severity", "warning")
    alertname = labels.get("alertname", "unknown")
    has_runbook = alertname in RUNBOOKS
    return severity, alertname, has_runbook


def circuit_breaker_tripped(alertname):
    """Límite duro: no más de MAX_ACTIONS_PER_HOUR acciones por alerta/hora."""
    now = time.time()
    history = action_history[alertname]
    while history and now - history[0] > WINDOW_SECONDS:
        history.popleft()
    return len(history) >= MAX_ACTIONS_PER_HOUR


def record_action(alertname):
    action_history[alertname].append(time.time())


def escalate_to_oncall(alertname, reason):
    """Simula notificar al on-call (en un caso real: PagerDuty/Slack API)."""
    log_event(
        event="escalate",
        alertname=alertname,
        reason=reason,
        channel="oncall-mock-webhook",
    )


def runbook_restart_service(alertname, alert):
    """Runbook idempotente: 'reinicia' el servicio afectado."""
    if alertname in resolved_incidents:
        log_event(event="skip_idempotent", alertname=alertname, reason="ya mitigado, esperando resolución")
        return "skipped_idempotent"

    if DRY_RUN:
        log_event(event="dry_run", alertname=alertname, action="restart_service")
        return "dry_run"

    # Acción real simulada (en producción: docker restart / kubectl rollout restart / Ansible).
    service = alert.get("labels", {}).get("service", "unknown-service")
    log_event(event="action_executed", alertname=alertname, action="restart_service", service=service)
    resolved_incidents.add(alertname)
    return "executed"


def runbook_scale_out(alertname, alert):
    """Runbook idempotente: escala horizontalmente el servicio afectado."""
    if alertname in resolved_incidents:
        log_event(event="skip_idempotent", alertname=alertname, reason="ya escalado, esperando resolución")
        return "skipped_idempotent"

    if DRY_RUN:
        log_event(event="dry_run", alertname=alertname, action="scale_out")
        return "dry_run"

    service = alert.get("labels", {}).get("service", "unknown-service")
    log_event(event="action_executed", alertname=alertname, action="scale_out", service=service, replicas="+2")
    resolved_incidents.add(alertname)
    return "executed"


RUNBOOKS = {
    "ServiceDown": runbook_restart_service,
    "HighCPULoad": runbook_scale_out,
}


@app.route("/webhook/alert", methods=["POST"])
def receive_alert():
    payload = request.get_json(force=True, silent=True) or {}
    alerts = payload.get("alerts", [payload])  # acepta payload completo de Alertmanager o una alerta suelta
    results = []

    for alert in alerts:
        status = alert.get("status", "firing")
        severity, alertname, has_runbook = classify(alert)

        log_event(event="alert_received", alertname=alertname, severity=severity, status=status)

        if status == "resolved":
            resolved_incidents.discard(alertname)
            log_event(event="incident_resolved", alertname=alertname)
            results.append({"alertname": alertname, "outcome": "resolved"})
            continue

        if not has_runbook:
            escalate_to_oncall(alertname, reason="sin runbook definido")
            results.append({"alertname": alertname, "outcome": "escalated_no_runbook"})
            continue

        if circuit_breaker_tripped(alertname):
            escalate_to_oncall(alertname, reason="circuit breaker: demasiadas acciones en la última hora")
            results.append({"alertname": alertname, "outcome": "escalated_circuit_breaker"})
            continue

        outcome = RUNBOOKS[alertname](alertname, alert)
        if outcome == "executed":
            record_action(alertname)

        if severity == "critical" and outcome != "dry_run":
            # Además de mitigar, avisamos igual al equipo por trazabilidad en incidentes críticos.
            escalate_to_oncall(alertname, reason="severidad critical, notificación informativa")

        results.append({"alertname": alertname, "outcome": outcome})

    return jsonify({"processed": results, "dry_run": DRY_RUN}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "dry_run": DRY_RUN, "max_actions_per_hour": MAX_ACTIONS_PER_HOUR})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
