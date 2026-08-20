# SRE vs DevOps: similitudes y diferencias

Post del blog: [SRE vs DevOps: similitudes y diferencias](https://www.devopsfreelance.pro/blog/posts/sre-vs-devops-similitudes-diferencias/)

## Qué demuestra este ejemplo

El post explica que la diferencia central entre DevOps y SRE es que **SRE cuantifica la
confiabilidad** con métricas concretas (SLO, Error Budget, toil), mientras que DevOps es
una filosofía que no prescribe cómo medirla.

Este ejemplo implementa esa idea con código ejecutable:

- `error_budget.py`: calcula el downtime permitido para un SLO dado, cuánto presupuesto de
  error queda tras un incidente real, y emite la recomendación típica de SRE ("seguir
  lanzando features" vs "congelar features y priorizar confiabilidad"). También calcula el
  ratio de **toil** (trabajo operativo manual) y lo compara contra el objetivo de SRE de
  mantenerlo por debajo del 50%.
- `test_error_budget.py`: tests unitarios sin dependencias externas que verifican los
  cálculos (incluye el mismo caso citado en el post: SLO 99.9% ≈ 43 minutos de downtime
  mensual permitido).

## Requisitos

- Python 3.8 o superior (solo librería estándar, sin `pip install`)

## Cómo correrlo

Desde este directorio:

```bash
# 1) Correr los tests
python3 test_error_budget.py

# 2) Caso "saludable": SLO 99.9%, mes de 720h (30 dias), 30 min de downtime real
python3 error_budget.py --slo 99.9 --period-hours 720 --downtime-minutes 30 \
  --toil-hours 20 --worked-hours 160

# 3) Caso "presupuesto agotado": mismo SLO, 100 min de downtime real
python3 error_budget.py --slo 99.9 --period-hours 720 --downtime-minutes 100
```

## Salida esperada

Paso 1 (tests):

```
OK   test_allowed_downtime_99_9
OK   test_budget_healthy
OK   test_budget_exhausted
OK   test_toil_within_target
OK   test_toil_above_target

Todos los tests pasaron.
```

Paso 2 (caso saludable, `--toil-hours`/`--worked-hours` opcionales):

```
=== Error Budget ===
SLO objetivo:            99.9%
Downtime permitido:      43.2 min
Downtime real:           30.0 min
Presupuesto restante:    13.2 min (30.56%)
Estado:                  healthy
Recomendacion:           OK para seguir desplegando nuevas features

=== Toil ===
Horas de toil:           20.0
Horas trabajadas:        160.0
Porcentaje de toil:      12.5%
Estado:                  dentro del objetivo (<50%)
```

Paso 3 (presupuesto agotado, exit code 1):

```
=== Error Budget ===
SLO objetivo:            99.9%
Downtime permitido:      43.2 min
Downtime real:           100.0 min
Presupuesto restante:    -56.8 min (-131.48%)
Estado:                  exhausted
Recomendacion:           Congelar features nuevas y priorizar confiabilidad
```

El script devuelve exit code `0` cuando el error budget está sano y `1` cuando está
agotado, para que se pueda encadenar en un pipeline de CI/CD como gate de decisión
("¿es seguro desplegar hoy?"), que es exactamente el mecanismo que describe el post.
