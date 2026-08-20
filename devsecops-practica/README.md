# DevSecOps en la práctica: pipeline de seguridad local

Ejemplo de código para el post [Guía Definitiva de DevSecOps Implementación en 2025](https://www.devopsfreelance.pro/blog/posts/devsecops-practica/).

## Qué demuestra

El post describe un pipeline DevSecOps con controles de seguridad en cada
etapa (Commit → SAST, Build → escaneo de dependencias, Deploy → escaneo de
contenedores). Este ejemplo reproduce esas tres etapas de forma real y
ejecutable contra una mini app Flask que tiene vulnerabilidades **puestas a
propósito**, para que cada herramienta encuentre algo:

| Etapa   | Herramienta | Qué detecta en este ejemplo                                    |
|---------|-------------|------------------------------------------------------------------|
| Commit  | Bandit (SAST) | `eval()` sobre input del usuario y `subprocess` con `shell=True` |
| Commit  | Gitleaks (secretos) | Una AWS access key hardcodeada (fake) en `app/app.py`    |
| Build   | Trivy (dependencias) | CVEs conocidas en `Flask==0.12.2` y `requests==2.19.1`   |
| Deploy  | Trivy (imagen) | CVEs del sistema operativo/paquetes en la imagen Docker final  |

Todas las herramientas corren dentro de contenedores Docker oficiales, así
que no hace falta instalar Bandit, Gitleaks ni Trivy en tu máquina.

## Requisitos

- Docker (con acceso a Docker Hub para bajar las imágenes `python:3.11-slim`,
  `zricethezav/gitleaks`, `aquasec/trivy`)
- Bash

## Cómo correrlo

```bash
cd devsecops-practica
./pipeline.sh
```

El script ejecuta, en orden, las 5 etapas del pipeline (SAST, secretos,
dependencias, build de imagen, escaneo de imagen) y termina con un resumen.
No hace falta ningún paso previo: el script descarga las imágenes de Docker
que necesita la primera vez que corre (puede tardar 1-2 minutos).

## Salida esperada

El script está pensado para que **falle a propósito** en varios pasos,
mostrando cómo un pipeline real bloquearía el commit/build/deploy:

```
1) SAST - Análisis estático de código con Bandit (etapa: Commit)
...
>> Issue: [B307:blacklist] Use of possibly insecure function - eval...
>> Issue: [B602:subprocess_popen_with_shell_equals_true] subprocess call with shell=True...
>> Bandit encontró hallazgos (esperado: eval(), shell=True).

2) Escaneo de secretos con Gitleaks (etapa: Commit)
...
Finding:     AWS_ACCESS_KEY_ID = "AKIAFAKEEXAMPLE1234"
>> Gitleaks encontró secretos (esperado: AWS key de ejemplo en app.py).

3) Escaneo de dependencias con Trivy (etapa: Build)
...
Flask   CVE-2018-1000656   HIGH ...
requests CVE-2018-18074    HIGH ...
>> Trivy encontró CVEs en las dependencias (esperado: Flask/requests viejos).

4) Build de la imagen (etapa: Build)
Successfully tagged devsecops-practica-app:latest

5) Escaneo de la imagen con Trivy (etapa: Deploy)
...
>> Trivy encontró CVEs en la imagen construida.

==================================================================
Pipeline DevSecOps: se detectaron hallazgos de seguridad (comportamiento
esperado en este demo). En un pipeline real, estos hallazgos bloquearían
el merge/deploy (shift left).
==================================================================
```

Los CVE exactos que reporte Trivy pueden variar según la fecha en que corras
el ejemplo (la base de datos de vulnerabilidades se actualiza continuamente),
pero siempre debería encontrar hallazgos HIGH/CRITICAL contra estas versiones
desactualizadas.

## Llevarlo a un pipeline real (CI/CD)

En GitHub Actions, cada uno de estos 5 pasos es un `step` del job, corriendo
las mismas imágenes de Docker (`docker run bandit ...`, acción oficial
`aquasecurity/trivy-action`, acción oficial `gitleaks/gitleaks-action`) con
`continue-on-error: false` para que un hallazgo HIGH/CRITICAL bloquee el
merge o el deploy, tal como describe el post en la sección "DevSecOps
Pipeline: Integrando Seguridad en cada Etapa".

## Estructura

```
devsecops-practica/
├── README.md
├── pipeline.sh          # orquesta las 5 etapas del pipeline
└── app/
    ├── app.py            # mini app Flask con vulnerabilidades intencionales
    ├── requirements.txt  # dependencias desactualizadas a propósito
    └── Dockerfile
```
