# SAST y DAST en CI/CD

Post: https://www.devopsfreelance.pro/blog/posts/sast-dast-pipelines-ci-cd/

## Que demuestra este ejemplo

La diferencia practica entre SAST y DAST que explica el post, usando la misma
app de ejemplo (`app.py`, una API Flask con vulnerabilidades sembradas a
proposito: SQL injection por concatenacion de strings, XSS reflejado y un
secreto hardcodeado):

- `run-sast.sh`: analiza el **codigo fuente sin ejecutar la app**, usando
  Semgrep con reglas de seguridad (`p/security-audit`, `p/secrets`,
  `p/sql-injection`). Detecta la inyeccion SQL por concatenacion de strings
  y el secreto hardcodeado, senalando la linea exacta.
- `run-dast.sh`: **despliega la app** en un contenedor y la ataca desde
  afuera con OWASP ZAP (baseline scan), como haria un atacante que no tiene
  acceso al codigo. Detecta la ausencia de headers de seguridad (CSP,
  X-Content-Type-Options, Permissions-Policy, anti-clickjacking, version
  del servidor expuesta), cosas que solo se ven con la app corriendo y que
  SAST no puede detectar analizando el codigo fuente.

Es la misma logica que en el pipeline del post: SAST temprano contra el
codigo, DAST mas tarde contra el entorno desplegado, ambos complementarios.

No incluye SCA ni escaneo de imagenes de contenedor (Snyk/Trivy) porque eso
ya esta cubierto en el ejemplo del post
[escaneo-vulnerabilidades-contenedores](../escaneo-vulnerabilidades-contenedores/).

## Requisitos

- Docker (con el daemon corriendo)
- Conexion a internet la primera vez, para bajar las imagenes
  `returntocorp/semgrep`, `ghcr.io/zaproxy/zaproxy` y `curlimages/curl`

No hace falta instalar Semgrep, ZAP ni Python en el host: todo corre como
contenedor.

## Pasos para correrlo

### 1. SAST (analisis estatico, sin desplegar nada)

```bash
cd sast-dast-pipelines-ci-cd
./run-sast.sh
```

### 2. DAST (build + deploy + ataque contra la app en ejecucion)

```bash
./run-dast.sh
```

El script construye la imagen, levanta la app en un contenedor, espera a que
responda, corre el scan de ZAP contra ella y al terminar borra el contenedor
y la red que creo (no deja nada corriendo).

## Salida esperada

### SAST (`run-sast.sh`)

Semgrep reporta 3 hallazgos y el script termina con exit code 1 (como
rompería un build real):

```
== SAST: Semgrep contra app.py (codigo estatico, app NO se ejecuta) ==
...
┌─────────────────┐
│ 3 Code Findings │
└─────────────────┘

/src/app.py
❯❯❱ python.flask.security.audit.hardcoded-config.avoid_hardcoded_config_SECRET_KEY
    Hardcoded variable `SECRET_KEY` detected. Use environment variables...
    19┆ app.config["SECRET_KEY"] = "super-secret-key-do-not-use-in-prod"

❯❱ python.django.security.injection.sql.sql-injection-using-db-cursor-execute...
    User-controlled data from a request is passed to 'execute()'...
    45┆ query = "SELECT id, name FROM users WHERE id = " + user_id

❯❱ python.flask.security.audit.app-run-param-config.avoid_app_run_with_bad_host
    Running flask app with host 0.0.0.0 could expose the server publicly.
    64┆ app.run(host="0.0.0.0", port=5000)

Reporte guardado en sast-report.txt
```

### DAST (`run-dast.sh`)

ZAP levanta la app, la escanea desde afuera (sin tocar el codigo fuente) y
genera `dast-report.html` con alertas de falta de headers de seguridad y
version del servidor expuesta, cosas que solo se detectan con la app
corriendo:

```
== DAST: OWASP ZAP baseline scan contra la app en ejecucion ==
...
WARN-NEW: Missing Anti-clickjacking Header [10020] x 1
WARN-NEW: X-Content-Type-Options Header Missing [10021] x 1
WARN-NEW: Server Leaks Version Information via "Server" HTTP Response Header Field [10036] x 3
WARN-NEW: Content Security Policy (CSP) Header Not Set [10038] x 2
WARN-NEW: Storable and Cacheable Content [10049] x 3
WARN-NEW: Permissions Policy Header Not Set [10063] x 3
WARN-NEW: Cross-Origin-Embedder-Policy Header Missing or Invalid [90004] x 3
FAIL-NEW: 0	FAIL-INPROG: 0	WARN-NEW: 7	WARN-INPROG: 0	INFO: 0	IGNORE: 0	PASS: 60
Reporte guardado en dast-report.html
```

El baseline scan de ZAP es pasivo (spidea y analiza respuestas, no envia
payloads de ataque activos), por eso no explota el XSS reflejado de
`/greet` ni la inyeccion SQL de `/user` — para eso existe el *full scan*
(`zap-full-scan.py`, el que usa el post) o un *active scan* explicito. El
baseline es el que se corre en pipelines normales por ser rapido y de bajo
riesgo; el full scan es mas lento y agresivo, pensado para staging.

Abrí `dast-report.html` en un navegador para ver el detalle de cada alerta
(URL, evidencia, riesgo, remediación sugerida), igual que en el reporte que
generaría el job `dast` del pipeline del post.

## Notas

- `SECRET_KEY` en `app.py` es un valor de ejemplo intencionalmente
  hardcodeado para que SAST lo detecte; nunca hagas esto en código real, usá
  variables de entorno o un secret manager.
- `run-sast.sh` termina con exit code 1 cuando Semgrep encuentra hallazgos,
  para ilustrar cómo este mismo comando rompería un job de CI/CD real.
- `run-dast.sh` usa `-I` en `zap-baseline.py`, que evita que el script falle
  aunque haya WARN (se eligió así para que el ejemplo termine siempre en
  verde y sea fácil de correr); en un pipeline real se saca el `-I` para que
  `zap-baseline.py` devuelva exit code distinto de cero ante WARN/FAIL y
  bloquee el build.
