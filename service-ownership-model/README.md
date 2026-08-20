# Service Ownership Model - Calculadora de Error Budget

Ejemplo de código para el post [Guía Completa de Service ownership model](https://www.devopsfreelance.pro/blog/posts/service-ownership-model/).

## Qué demuestra

El post explica que el error budget no es solo una métrica de disponibilidad,
sino una **herramienta de decisión** para el equipo owner de un servicio:
si el budget está sano, el equipo puede asumir más riesgo (deployments
frecuentes, features experimentales); si está bajo, debe priorizar
estabilidad.

Este ejemplo implementa esa lógica en un script Python:

- Lee la definición de SLOs de un servicio (`slo_config.yaml`), con el mismo
  formato usado en el post (SLI, target, ventana).
- Lee 30 días de métricas de tráfico simuladas (`sample_metrics.csv`),
  incluyendo un incidente de 2 días (3-4 de agosto) que dispara errores y
  latencia.
- Calcula, para cada SLO: porcentaje alcanzado, eventos "malos" consumidos
  vs. permitidos, porcentaje de budget consumido y **burn rate** (velocidad
  de consumo vs. lo esperado para ese punto de la ventana).
- Imprime una recomendación operativa concreta, y termina con exit code 1
  si algún SLO agotó su budget (útil para engancharlo a un pipeline de
  CI/CD que bloquee deployments no críticos cuando el budget está en rojo).

No implementa PagerDuty, Backstage ni el resto del ecosistema mencionado en
el post: el objetivo es ilustrar el concepto central (SLO -> error budget ->
decisión), no replicar todas las herramientas.

## Requisitos

- Python 3.8+
- Librería `PyYAML`

## Cómo correrlo

```bash
cd service-ownership-model

# Instalar la única dependencia
pip install pyyaml

# Correr con los archivos de ejemplo incluidos
python3 error_budget_calculator.py
```

También podés apuntar a tus propios archivos:

```bash
python3 error_budget_calculator.py --slo slo_config.yaml --metrics sample_metrics.csv
```

## Salida esperada

```
Servicio: payment-api  |  Owner: Team Payments
Ventana: 30 dias  |  Dias con datos: 30
Requests totales en el periodo: 3041609

--- SLO: Availability ---
  Target:            99.950%
  Alcanzado:         99.8788%
  Eventos malos:     3686 (permitidos: 1520.8)
  Budget consumido:  242.4%
  Recomendacion:     BUDGET AGOTADO (burn rate 2.4x). Congelar deployments no criticos, priorizar estabilidad y root-cause del incidente que lo consumio.

--- SLO: Latency ---
  Target:            99.000%
  Alcanzado:         99.1885%
  Eventos malos:     24684 (permitidos: 30416.1)
  Budget consumido:  81.2%
  Recomendacion:     BUDGET BAJO (burn rate 0.8x). Reducir frecuencia de deployments, invertir en tests y resiliencia antes de tomar mas riesgo.
```

El script termina con exit code `1` porque el SLO de Availability agotó su
budget (el incidente simulado del 3-4 de agosto consumió más del 100% del
error budget permitido para los 30 días).

## Archivos

- `slo_config.yaml` - Definición de los SLOs del servicio `payment-api`
  (mismo formato que la sección "SLOs por equipo" del post).
- `sample_metrics.csv` - 30 días de métricas diarias simuladas
  (`total_requests`, `failed_requests`, `slow_requests`), con un incidente
  el 3-4 de agosto.
- `error_budget_calculator.py` - Script que calcula el consumo de budget y
  la recomendación operativa.

## Adaptarlo a un servicio real

Para usar esto con datos reales, reemplazá `sample_metrics.csv` por una
exportación de tu sistema de métricas (Prometheus, Datadog, CloudWatch,
etc.) con las mismas columnas, y ajustá `slo_config.yaml` con los SLOs
reales de tu servicio y su equipo owner.
