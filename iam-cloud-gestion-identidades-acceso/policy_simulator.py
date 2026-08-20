#!/usr/bin/env python3
"""
policy_simulator.py

Simulador minimo del motor de evaluacion de politicas IAM de AWS.
Reproduce las reglas centrales descritas en el post "IAM Cloud: Gestion de
Identidades y Acceso en DevOps 2025":

  1. Deny explicito siempre gana.
  2. Sin un Allow explicito que matchee, el resultado es Deny implicito
     (default deny).
  3. Un permission boundary limita el maximo de permisos efectivos: el
     resultado final es Allow solo si TANTO la politica de identidad COMO
     el boundary lo permiten.
  4. Las condiciones (IpAddress, BoolIfExists sobre MFA) pueden hacer que
     un statement no aplique.

No requiere cuenta de AWS, Docker ni dependencias externas: solo la
biblioteca estandar de Python 3.

Uso:
    python3 policy_simulator.py
"""

import fnmatch
import ipaddress
import json
import os
import sys

POLICIES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "policies")


def load_policy(filename):
    path = os.path.join(POLICIES_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _action_matches(statement, action):
    """Devuelve True si el statement aplica a esta accion, considerando
    Action (lista positiva) o NotAction (lista negativa)."""
    if "Action" in statement:
        return any(fnmatch.fnmatchcase(action, p) for p in _as_list(statement["Action"]))
    if "NotAction" in statement:
        return not any(fnmatch.fnmatchcase(action, p) for p in _as_list(statement["NotAction"]))
    return False


def _resource_matches(statement, resource):
    if "Resource" not in statement:
        return True  # statements sin Resource (ej: solo NotAction) se tratan como "*"
    return any(fnmatch.fnmatchcase(resource, p) for p in _as_list(statement["Resource"]))


def _condition_matches(statement, context):
    """Evalua el bloque Condition del statement contra el contexto de la
    request. Soporta los operadores usados en el post: IpAddress,
    StringEquals y BoolIfExists."""
    condition = statement.get("Condition")
    if not condition:
        return True

    for operator, checks in condition.items():
        for context_key, expected in checks.items():
            actual = context.get(context_key)

            if operator == "IpAddress":
                if actual is None:
                    return False
                network = ipaddress.ip_network(expected, strict=False)
                if ipaddress.ip_address(actual) not in network:
                    return False

            elif operator == "StringEquals":
                if actual != expected:
                    return False

            elif operator == "BoolIfExists":
                # Si el contexto no trae el valor, se asume "false"
                # (comportamiento real de aws:MultiFactorAuthPresent).
                actual_bool = "true" if actual else "false"
                if actual_bool != str(expected).lower():
                    return False

            else:
                raise NotImplementedError(f"Operador de condicion no soportado: {operator}")

    return True


def evaluate_policy(policy_doc, action, resource, context=None):
    """Evalua un unico documento de politica IAM contra una request.

    Retorna "Allow" o "Deny" (implicito o explicito) siguiendo el orden
    real de AWS: cualquier Deny explicito que matchee gana sobre cualquier
    Allow; si no hay Allow que matchee, el resultado es Deny implicito.
    """
    context = context or {}
    has_matching_allow = False

    for statement in policy_doc.get("Statement", []):
        if not _action_matches(statement, action):
            continue
        if not _resource_matches(statement, resource):
            continue
        if not _condition_matches(statement, context):
            continue

        if statement.get("Effect") == "Deny":
            return "Deny"  # deny explicito: corta evaluacion inmediatamente
        if statement.get("Effect") == "Allow":
            has_matching_allow = True

    return "Allow" if has_matching_allow else "Deny"


def evaluate_with_boundary(identity_policy, boundary_policy, action, resource, context=None):
    """Combina una politica de identidad con un permission boundary.

    El resultado efectivo es Allow unicamente si ambas evaluaciones dan
    Allow: el boundary nunca otorga permisos por si solo, solo los acota.
    """
    identity_decision = evaluate_policy(identity_policy, action, resource, context)
    boundary_decision = evaluate_policy(boundary_policy, action, resource, context)

    if identity_decision == "Allow" and boundary_decision == "Allow":
        return "Allow"
    return "Deny"


def run_demo():
    failures = []

    def check(label, actual, expected):
        status = "OK" if actual == expected else "FAIL"
        print(f"[{status}] {label}: esperado={expected} obtenido={actual}")
        if actual != expected:
            failures.append(label)

    print("=== 1. Least privilege S3 (policies/least-privilege-s3.json) ===")
    s3_policy = load_policy("least-privilege-s3.json")

    check(
        "GetObject desde IP de la VPC (10.1.2.3) -> permitido",
        evaluate_policy(
            s3_policy,
            "s3:GetObject",
            "arn:aws:s3:::my-app-data/report.csv",
            {"aws:SourceIp": "10.1.2.3"},
        ),
        "Allow",
    )
    check(
        "GetObject desde IP publica (203.0.113.5) -> denegado por condicion",
        evaluate_policy(
            s3_policy,
            "s3:GetObject",
            "arn:aws:s3:::my-app-data/report.csv",
            {"aws:SourceIp": "203.0.113.5"},
        ),
        "Deny",
    )
    check(
        "DeleteObject desde la VPC -> denegado (accion no otorgada)",
        evaluate_policy(
            s3_policy,
            "s3:DeleteObject",
            "arn:aws:s3:::my-app-data/report.csv",
            {"aws:SourceIp": "10.1.2.3"},
        ),
        "Deny",
    )

    print()
    print("=== 2. Permission boundary (policies/permission-boundary.json) ===")
    broad_identity_policy = load_policy("broad-identity-policy.json")
    boundary_policy = load_policy("permission-boundary.json")

    check(
        "Rol con politica amplia + boundary: s3:PutObject -> permitido (dentro del boundary)",
        evaluate_with_boundary(broad_identity_policy, boundary_policy, "s3:PutObject", "*"),
        "Allow",
    )
    check(
        "Rol con politica amplia + boundary: iam:CreateUser -> denegado (fuera del boundary)",
        evaluate_with_boundary(broad_identity_policy, boundary_policy, "iam:CreateUser", "*"),
        "Deny",
    )

    print()
    print("=== 3. MFA enforcement (policies/mfa-enforcement.json) ===")
    mfa_policy = load_policy("mfa-enforcement.json")

    check(
        "s3:GetObject sin MFA -> denegado (DenyAllExceptMFASetup aplica)",
        evaluate_policy(
            mfa_policy, "s3:GetObject", "arn:aws:s3:::my-app-data/report.csv",
            {"aws:MultiFactorAuthPresent": False},
        ),
        "Deny",
    )
    check(
        "iam:CreateVirtualMFADevice sin MFA -> permitido (excepcion via NotAction)",
        evaluate_policy(
            mfa_policy, "iam:CreateVirtualMFADevice",
            "arn:aws:iam::123456789012:mfa/${aws:username}",
            {"aws:MultiFactorAuthPresent": False},
        ),
        "Allow",
    )
    check(
        "s3:GetObject con MFA presente -> el deny de este statement ya no aplica",
        evaluate_policy(
            mfa_policy, "s3:GetObject", "arn:aws:s3:::my-app-data/report.csv",
            {"aws:MultiFactorAuthPresent": True},
        ),
        # Con MFA presente, DenyAllExceptMFASetup no matchea. Esta politica
        # por si sola tampoco otorga s3:GetObject (esa concesion vendria de
        # otra politica adjunta, como least-privilege-s3.json), por eso el
        # resultado sigue siendo Deny implicito, pero ya NO por el deny
        # explicito de "falta de MFA".
        "Deny",
    )

    print()
    if failures:
        print(f"RESULTADO: {len(failures)} verificacion(es) fallaron: {failures}")
        sys.exit(1)
    print("RESULTADO: todas las verificaciones pasaron correctamente.")


if __name__ == "__main__":
    run_demo()
