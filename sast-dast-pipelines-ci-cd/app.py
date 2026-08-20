"""
App de ejemplo INTENCIONALMENTE vulnerable, usada solo para que SAST y DAST
tengan algo que detectar. No usar este codigo como referencia de como escribir
una app Flask real.

Vulnerabilidades a proposito:
- SQL injection en /user (concatenacion de strings en la query)
- XSS reflejado en /greet (el input del usuario se vuelca sin escapar)
- Secreto hardcodeado (SECRET_KEY)
- Header de seguridad ausente (no Content-Security-Policy, etc.)
"""
import sqlite3

from flask import Flask, request

app = Flask(__name__)

# Vulnerabilidad SAST: secreto hardcodeado en el codigo fuente.
app.config["SECRET_KEY"] = "super-secret-key-do-not-use-in-prod"

DB_PATH = "/tmp/demo.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER, name TEXT)")
    conn.execute("DELETE FROM users")
    conn.execute("INSERT INTO users VALUES (1, 'alice')")
    conn.execute("INSERT INTO users VALUES (2, 'bob')")
    conn.commit()
    conn.close()


@app.route("/")
def index():
    return "Demo app SAST/DAST - endpoints: /user?id=, /greet?name="


@app.route("/user")
def get_user():
    user_id = request.args.get("id", "1")
    conn = sqlite3.connect(DB_PATH)
    # Vulnerabilidad SAST: SQL injection, la query se arma por concatenacion
    # de strings en vez de usar parametros bindeados.
    query = "SELECT id, name FROM users WHERE id = " + user_id
    try:
        cursor = conn.execute(query)
        rows = cursor.fetchall()
    except sqlite3.OperationalError as exc:
        rows = [("error", str(exc))]
    conn.close()
    return {"query": query, "rows": rows}


@app.route("/greet")
def greet():
    name = request.args.get("name", "mundo")
    # Vulnerabilidad DAST: XSS reflejado, el input llega al HTML sin escapar.
    return f"<html><body><h1>Hola, {name}!</h1></body></html>"


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
