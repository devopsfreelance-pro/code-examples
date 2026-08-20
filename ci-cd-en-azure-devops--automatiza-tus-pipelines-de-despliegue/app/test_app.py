"""
Pruebas unitarias que el stage 'Build and Test' del pipeline ejecutaría
(equivalente local a la tarea DotNetCoreCLI@2 'Run unit tests' del post,
pero en Python con pytest para no requerir instalar el SDK de .NET).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import build_health_payload


def test_health_payload_status_ok():
    payload = build_health_payload()
    assert payload["status"] == "ok"


def test_health_payload_service_name():
    payload = build_health_payload()
    assert payload["service"] == "myapp"


def test_health_payload_uses_environment_variable(monkeypatch):
    monkeypatch.setenv("APP_ENVIRONMENT", "staging")
    payload = build_health_payload()
    assert payload["environment"] == "staging"


def test_health_payload_defaults_to_development(monkeypatch):
    monkeypatch.delenv("APP_ENVIRONMENT", raising=False)
    payload = build_health_payload()
    assert payload["environment"] == "development"
