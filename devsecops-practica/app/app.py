"""
Mini app de ejemplo con vulnerabilidades intencionales para que el pipeline
DevSecOps las detecte:
  - Secreto hardcodeado (para gitleaks)
  - subprocess con shell=True (para bandit / SAST)
  - eval() sobre input externo (para bandit / SAST)
  - dependencia desactualizada con CVEs conocidas (ver requirements.txt)
"""
import subprocess

from flask import Flask, request

app = Flask(__name__)

# Secreto hardcodeado de EJEMPLO (fake, no es una credencial real) para que
# gitleaks lo detecte en el escaneo de secretos.
AWS_ACCESS_KEY_ID = "AKIAFAKEEXAMPLE1234"


@app.route("/")
def index():
    return "DevSecOps demo app - ver /run y /calc"


@app.route("/run")
def run_command():
    """Vulnerabilidad intencional: shell=True con input del usuario (B602/B605)."""
    host = request.args.get("host", "localhost")
    result = subprocess.run(f"ping -c 1 {host}", shell=True, capture_output=True)
    return result.stdout


@app.route("/calc")
def calc():
    """Vulnerabilidad intencional: eval() sobre input del usuario (B307)."""
    expression = request.args.get("expr", "1+1")
    return str(eval(expression))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
