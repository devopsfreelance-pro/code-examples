"""
Tests unitarios de la fase "Test" del ciclo de vida DevOps.

Se corren con: python3 -m unittest test_app.py -v
Y son los mismos tests que ejecuta el pipeline de CI en .github/workflows/ci.yml
"""

import unittest

from app import APP_VERSION, health_payload, root_payload


class TestHealthPayload(unittest.TestCase):
    def test_status_is_ok(self) -> None:
        self.assertEqual(health_payload()["status"], "ok")

    def test_includes_version(self) -> None:
        self.assertEqual(health_payload()["version"], APP_VERSION)


class TestRootPayload(unittest.TestCase):
    def test_includes_message(self) -> None:
        self.assertEqual(root_payload()["message"], "Hola DevOps")

    def test_includes_version(self) -> None:
        self.assertEqual(root_payload()["version"], APP_VERSION)


if __name__ == "__main__":
    unittest.main()
