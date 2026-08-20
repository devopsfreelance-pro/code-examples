# Security Testing Automatizado - Ejemplo Ejecutable

Post relacionado: [Security Testing Automatizado: Guía Completa para DevSecOps](https://www.devopsfreelance.pro/blog/posts/security-testing-automatizado/)

## Qué demuestra este ejemplo

Una versión mínima y ejecutable del pipeline de security testing descripto en el
post: en vez de correrlo dentro de GitHub Actions, lo reproducimos localmente
con Docker para que se pueda ver el resultado en minutos.

El ejemplo incluye:

- `app/app.py`: una mini aplicación Flask con **dos vulnerabilidades
  intencionales** (inyección SQL por concatenación de strings y un secreto
  hardcodeado en el código), pensadas específicamente para que el análisis
  SAST las detecte.
- `Dockerfile`: empaqueta esa app sobre una base image deliberadamente vieja
  (`python:3.9-slim-bullseye`) para que el escaneo de contenedor encuentre
  CVEs conocidos del sistema operativo base.
- `security-scan.sh`: orquesta dos de las capas de análisis que describe el
  post:
  1. **SAST** con [Semgrep](https://semgrep.dev/) (reglas `p/security-audit`
     y `p/owasp-top-ten`) contra `app/app.py`.
  2. **Escaneo de imagen de contenedor** con
     [Trivy](https://aquasecurity.github.io/trivy/) contra la imagen
     construida a partir del `Dockerfile`.

No requiere instalar Semgrep ni Trivy localmente: ambos corren como
contenedores Docker, sin cuentas ni licencias pagas.

## Requisitos

- Docker (con acceso a Docker Hub para bajar las imágenes `python`,
  `returntocorp/semgrep` y `aquasec/trivy`, y acceso al socket de Docker
  para que Trivy pueda inspeccionar la imagen construida localmente).
- Bash.

No hace falta ningún secreto ni API key: es todo local.

## Cómo correrlo

```bash
cd security-testing-automatizado
./security-scan.sh
```

El script:

1. Corre Semgrep contra `app/app.py` y guarda el resultado en
   `security-reports/semgrep-<timestamp>.json`.
2. Construye la imagen `vulnerable-app:test` a partir del `Dockerfile`.
3. Corre Trivy contra esa imagen (severidades `HIGH` y `CRITICAL`) y guarda
   el resultado en `security-reports/trivy-<timestamp>.json`.
4. Imprime un resumen y termina con código de salida `1` si Semgrep reportó
   hallazgos o si Trivy encontró vulnerabilidades `CRITICAL` (mismo patrón de
   gate que usa el pipeline de CI/CD del post).

## Salida esperada

Semgrep debería marcar como mínimo dos hallazgos en `app/app.py`:

- Inyección SQL en la construcción de la query dentro de `get_user()`.
- Secreto hardcodeado en `app.config["SECRET_KEY"]`.

Trivy debería reportar varias vulnerabilidades `HIGH`/`CRITICAL` en los
paquetes del sistema operativo de la imagen base `python:3.9-slim-bullseye`
(la cantidad exacta varía con el tiempo, a medida que se descubren y
publican nuevos CVEs).

Al final vas a ver algo similar a:

```
=== Resumen ==="
Reportes generados en: security-reports/
Semgrep: hallazgos SAST en app/app.py (inyeccion SQL + secreto hardcodeado esperados)
Trivy: 3 vulnerabilidades CRITICAL, 12 HIGH en la imagen base

FALLO: se encontraron vulnerabilidades. Revisa security-reports/
```

Ese código de salida distinto de cero es exactamente el comportamiento que,
en un pipeline real de GitHub Actions como el del post, bloquearía el merge
o el despliegue hasta corregir los hallazgos.

## Cómo llevarlo a un pipeline real

Este mismo patrón (build de la imagen, escaneo con Trivy, análisis con
Semgrep, gate por severidad) es el que arma el workflow de GitHub Actions
del post. Para adaptarlo, reemplazá los `docker run` de este script por los
steps `returntocorp/semgrep-action` y `aquasecurity/trivy-action` que
aparecen en el YAML del artículo.
