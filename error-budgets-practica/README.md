# Error Budgets en Practica: calculadora + gate de despliegue

Ejemplo de codigo que acompaña al post [Guía Completa de Error budgets en práctica](https://www.devopsfreelance.pro/blog/posts/error-budgets-practica/).

## Que demuestra

El post explica el concepto de error budget (cuanta indisponibilidad permite
un SLO) y un `ErrorBudgetGate` que decide si un despliegue puede proceder
segun el budget restante y el burn rate. Este ejemplo implementa esa logica
de forma completa y ejecutable:

- `error_budget_report.py`: genera 30 dias de trafico horario sintetico
  (con dos incidentes inyectados: uno agudo de 1 hora y uno sostenido de
  6 horas), calcula el error budget restante contra un SLO del 99.9% y
  evalua el burn rate en ventanas de 1h y 6h usando los umbrales estandar
  de Google SRE (14.4x / 6.0x). El script termina con exit code 0 si el
  despliegue esta permitido y 1 si esta bloqueado, tal como lo usaria un
  step de CI/CD.
- `prometheus_alert_rules.yml`: las mismas reglas de burn rate traducidas
  a alertas de Prometheus, listas para copiar a un stack real que exponga
  la metrica `http_requests_total`.

No incluye el caso de "SLIs mal definidos" ni los error budgets
jerarquicos de microservicios del post (son decisiones de arquitectura,
no algo que tenga sentido simular en un mini-ejemplo).

## Requisitos

- Python 3.9 o superior (solo libreria estandar, sin `pip install`)
- Opcional, solo para validar el YAML: `pip install pyyaml`

## Como correrlo

```bash
cd error-budgets-practica
python3 error_budget_report.py
```

Salida esperada (30 dias completos, sin incidente reciente en las ventanas
de burn rate, despliegue permitido):

```
============================================================
REPORTE DE ERROR BUDGET
============================================================
SLO objetivo:              99.90%
Ventana evaluada:          720 horas (30 dias)
Requests totales:          7,240,237
Errores totales:           4,324
Tasa de error observada:   0.0597%
Tasa de error permitida:   0.1000%
------------------------------------------------------------
Error budget restante:     40.3%
Burn rate (ventana 1h):    0.74x
Burn rate (ventana 6h):    0.58x
------------------------------------------------------------
Despliegue:                PERMITIDO
Motivo:                    Budget suficiente y burn rate dentro de rango normal
============================================================
```

El exit code es `0` en este caso (`echo $?`).

### Ver el gate bloqueando un despliegue

Para ver el caso donde el incidente sostenido (inyectado en las horas
700-705 de la simulacion) todavia esta dentro de la ventana de evaluacion,
cortá la simulacion justo despues del incidente con `--hours 706`:

```bash
python3 error_budget_report.py --hours 706
```

Salida esperada:

```
============================================================
REPORTE DE ERROR BUDGET
============================================================
SLO objetivo:              99.90%
Ventana evaluada:          706 horas (29 dias)
Requests totales:          7,104,643
Errores totales:           4,252
Tasa de error observada:   0.0598%
Tasa de error permitida:   0.1000%
------------------------------------------------------------
Error budget restante:     40.2%
Burn rate (ventana 1h):    11.92x
Burn rate (ventana 6h):    11.93x
------------------------------------------------------------
Despliegue:                BLOQUEADO
Motivo:                    Burn rate elevado y sostenido en ventana de 6h: 11.9x (umbral 6.0x)
============================================================
```

Exit code `1`, listo para hacer que un pipeline falle el step
`error_budget_check`.

### Opciones

```bash
python3 error_budget_report.py --help
```

- `--slo`: SLO objetivo como fraccion, por defecto `0.999` (99.9%)
- `--hours`: horas de trafico sintetico a simular, por defecto `720` (30 dias)
- `--seed`: seed del generador de trafico, por defecto `42` (misma salida siempre)
- `--min-budget`: budget minimo requerido para permitir el despliegue, por defecto `0.20` (20%)

### Validar las reglas de Prometheus

```bash
python3 -c "import yaml; yaml.safe_load(open('prometheus_alert_rules.yml')); print('YAML valido')"
```

No requiere un Prometheus corriendo; es solo validacion de sintaxis. Para
usarlas de verdad, copialas al `rule_files` de una instancia de Prometheus
que ya scrapee metricas `http_requests_total{status=...}` de tu servicio.

## Notas

- El trafico es sintetico (generado con seed fija para reproducibilidad),
  no proviene de ningun servicio real ni requiere credenciales.
- Los umbrales de burn rate (14.4x en 1h, 6x en 6h) son los que documenta
  el [Google SRE Workbook](https://sre.google/workbook/alerting-on-slos/)
  para un SLO mensual del 99.9%.
