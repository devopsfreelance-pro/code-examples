# Continuous improvement en DevOps: pipeline de metricas de calidad

Ejemplo de código que acompaña al post [Guía Completa de Continuous improvement en devops](https://www.devopsfreelance.pro/blog/posts/continuous-improvement-devops/).

## Qué demuestra

El post incluye un pipeline de ejemplo (sección "Implementación de pipelines
de mejora continua") que en cada commit corre análisis estático (pylint),
cobertura de pruebas y complejidad ciclomática (radon), y publica esas
métricas a un dashboard para poder responder: *¿la calidad del código está
mejorando o deteriorándose de una iteración a otra?*

Este ejemplo implementa exactamente ese pipeline de forma local y
ejecutable, aplicado a un caso concreto de kaizen: un mismo módulo
(`sample_app/calculator.py`) reescrito en 3 iteraciones sucesivas, simulando
3 ciclos de retrospectiva:

- **v1**: lógica monolítica en un único `if/elif` anidado, sin docstrings.
- **v2**: primera mejora kaizen, cada operación separada en su propia
  función (baja la complejidad ciclomática).
- **v3**: segunda mejora kaizen, se agregan type hints y manejo explícito
  de errores (dividir por cero deja de devolver `0` en silencio).

`run_demo.sh` corre, para cada iteración, el mismo trío de herramientas del
pipeline del post (pylint, radon, pytest --cov) contra la versión
correspondiente del código y guarda el resultado en `metrics_history.json`.
Al final, `scripts/show_trend.py` compara las 3 iteraciones entre sí y
emite un veredicto de mejora/empeoro por métrica, que es el paso "Check"
del ciclo PDCA que describe el post.

No incluye el resto del pipeline del post (seguridad con `safety`,
publicación a un dashboard de Grafana): quedan fuera del alcance de un demo
local sin servicios externos. La comparación de métricas DORA entre sprints
(deployment frequency, lead time, MTTR, change failure rate) ya está
cubierta en [`../kaizen-devops-mejora-continua/`](../kaizen-devops-mejora-continua/),
por lo que no se repite acá.

## Requisitos

- Docker (`docker version`). No hace falta Python instalado en el host: todo
  corre dentro del contenedor.

## Cómo correrlo

```bash
cd continuous-improvement-devops
docker build -t kaizen-demo .
docker run --rm kaizen-demo
```

## Salida esperada

```
[v1] pylint_issues=2 complexity_avg=6.0 coverage_pct=84.6%
[v2] pylint_issues=0 complexity_avg=1.4 coverage_pct=87.5%
[v3] pylint_issues=0 complexity_avg=1.4 coverage_pct=88.2%

iteracion  pylint_issues   complexity_avg   coverage_pct
v1         2               6.0              84.6
v2         0               1.4              87.5
v3         0               1.4              88.2

=== Tendencia entre iteraciones (ciclo PDCA: paso Check) ===

v1 -> v2:
  pylint_issues: 2 -> 0  (mejora)
  complexity_avg: 6.0 -> 1.4  (mejora)
  coverage_pct: 84.6 -> 87.5  (mejora)

v2 -> v3:
  pylint_issues: 0 -> 0  (sin cambio)
  complexity_avg: 1.4 -> 1.4  (sin cambio)
  coverage_pct: 87.5 -> 88.2  (mejora)
```

Los números exactos de pylint/radon pueden variar levemente según la
versión de las herramientas, pero la tendencia se mantiene: el salto grande
ocurre entre v1 y v2 (separar el `if/elif` monolítico en funciones baja la
complejidad de 6.0 a 1.4 y elimina los 2 issues de pylint). Entre v2 y v3,
pylint y complejidad quedan iguales porque agregar type hints y manejo de
errores no cambia la estructura del código, solo su robustez; la cobertura
sigue subiendo porque los tests nuevos ejercitan las mismas rutas. Es el
punto que señala el post: no toda mejora kaizen mueve todas las métricas a
la vez, y por eso el pipeline las mide todas en cada iteración en lugar de
asumir que un refactor es "mejor" sin datos.

## Correrlo sin Docker

Si preferís no usar Docker, con Python 3.10+:

```bash
cd continuous-improvement-devops
pip install -r requirements.txt
touch sample_app/__init__.py tests/__init__.py
bash run_demo.sh
```

## Adaptarlo a un pipeline real

Para usarlo en un pipeline de CI real (el YAML del post es GitHub Actions),
reemplazá el bucle de `run_demo.sh` por un solo `python3
scripts/collect_metrics.py <sha-del-commit>` en cada push, y hacé que
`metrics_history.json` se acumule en un artefacto persistente (o se publique
a un dashboard como Grafana) en vez de reiniciarse en cada corrida.
