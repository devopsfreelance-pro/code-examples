"""
Mini aplicacion Flask CON vulnerabilidades intencionales.

Sirve como blanco de prueba para el pipeline de security testing:
- SAST (Semgrep) debe detectar la inyeccion SQL y el secreto hardcodeado.
- El Dockerfile que la empaqueta usa una base image vieja a proposito
  para que el escaneo de contenedor (Trivy) encuentre CVEs conocidos.

NO USAR EN PRODUCCION. Es material de laboratorio.
"""
import sqlite3

from flask import Flask, request

app = Flask(__name__)

# Vulnerabilidad 1: secreto hardcodeado en el codigo fuente.
# Semgrep (regla generic.secrets / owasp-top-ten) debe marcar esta linea.
app.config["SECRET_KEY"] = "super-secret-key-do-not-use-in-prod"

DB_PATH = "/tmp/users.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)"
    )
    conn.execute("INSERT OR IGNORE INTO users (id, username) VALUES (1, 'admin')")
    conn.commit()
    conn.close()


@app.route("/users")
def get_user():
    """Endpoint vulnerable a inyeccion SQL.

    Ejemplo de explotacion: /users?username=' OR '1'='1
    """
    username = request.args.get("username", "")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Vulnerabilidad 2: inyeccion SQL por concatenacion de strings.
    # Semgrep (regla python.flask.security.injection.sql-injection-db-cursor-execute)
    # debe marcar esta linea.
    query = "SELECT id, username FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    return {"results": rows}


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
