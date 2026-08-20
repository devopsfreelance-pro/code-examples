#!/usr/bin/env python3
"""
Motor de evaluacion de politicas IAM estilo AWS.

Implementa el algoritmo real que usa AWS IAM (y que aplica igual en Azure/GCP
con otros nombres): "deny explicito siempre gana", despues "algun allow que
matchee accion+recurso+condiciones", si no hay match -> deny implicito.

No depende de AWS ni de ningun servicio externo: es el mismo concepto del
post ("Autorizacion" con ABAC/RBAC/condiciones) reducido a su nucleo logico,
para poder ejecutarlo y ver el resultado en segundos.
"""
import fnmatch
import ipaddress
import json
import sys
from pathlib import Path


def _matches_pattern(value: str, patterns) -> bool:
    if isinstance(patterns, str):
        patterns = [patterns]
    return any(fnmatch.fnmatch(value, p) for p in patterns)


def _condition_matches(condition: dict, context: dict) -> bool:
    """Evalua el bloque "Condition" de una policy contra el contexto de la request."""
    if not condition:
        return True

    for operator, checks in condition.items():
        for ctx_key, expected in checks.items():
            actual = context.get(ctx_key)

            if operator == "IpAddress":
                if actual is None:
                    return False
                nets = expected if isinstance(expected, list) else [expected]
                if not any(ipaddress.ip_address(actual) in ipaddress.ip_network(n) for n in nets):
                    return False

            elif operator == "NotIpAddress":
                if actual is None:
                    return False
                nets = expected if isinstance(expected, list) else [expected]
                if any(ipaddress.ip_address(actual) in ipaddress.ip_network(n) for n in nets):
                    return False

            elif operator == "Bool":
                expected_bool = str(expected).lower() == "true"
                if str(actual).lower() != str(expected_bool).lower():
                    return False

            elif operator == "StringEquals":
                values = expected if isinstance(expected, list) else [expected]
                if actual not in values:
                    return False

            else:
                raise ValueError(f"Operador de condicion no soportado: {operator}")

    return True


def evaluate(policies: list, action: str, resource: str, context: dict) -> dict:
    """
    Devuelve {"decision": "Allow"|"Deny", "reason": str}.

    Regla de AWS: un Deny explicito en cualquier policy gana siempre.
    Si no hay Deny, se necesita al menos un Allow que matchee.
    Sin ningun match -> deny implicito.
    """
    matched_allow = None
    for policy in policies:
        for statement in policy.get("Statement", []):
            if not _matches_pattern(action, statement.get("Action", [])):
                continue
            if not _matches_pattern(resource, statement.get("Resource", [])):
                continue
            if not _condition_matches(statement.get("Condition", {}), context):
                continue

            effect = statement["Effect"]
            sid = statement.get("Sid", "(sin Sid)")

            if effect == "Deny":
                return {
                    "decision": "Deny",
                    "reason": f"Deny explicito en statement '{sid}' de policy '{policy['policy_name']}'",
                }
            if effect == "Allow" and matched_allow is None:
                matched_allow = f"Allow en statement '{sid}' de policy '{policy['policy_name']}'"

    if matched_allow:
        return {"decision": "Allow", "reason": matched_allow}
    return {"decision": "Deny", "reason": "Deny implicito: ningun Allow matcheo accion+recurso+condiciones"}


def load_policies(policies_dir: Path) -> list:
    policies = []
    for path in sorted(policies_dir.glob("*.json")):
        with open(path) as f:
            data = json.load(f)
        data["policy_name"] = path.stem
        policies.append(data)
    return policies


def main():
    base = Path(__file__).parent
    policies = load_policies(base / "policies")

    with open(base / "requests.json") as f:
        requests = json.load(f)

    exit_code = 0
    for req in requests:
        result = evaluate(
            policies,
            action=req["action"],
            resource=req["resource"],
            context=req.get("context", {}),
        )
        status = "OK " if result["decision"] == req["expected"] else "FALLO"
        if result["decision"] != req["expected"]:
            exit_code = 1

        print(f"[{status}] {req['description']}")
        print(f"       accion={req['action']} recurso={req['resource']}")
        print(f"       decision={result['decision']} (esperado={req['expected']})")
        print(f"       motivo: {result['reason']}")
        print()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
