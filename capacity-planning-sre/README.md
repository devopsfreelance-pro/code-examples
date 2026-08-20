# Capacity Planning para SRE: mini ejemplo ejecutable

Post relacionado: [Capacity planning para sre](https://www.devopsfreelance.pro/blog/posts/capacity-planning-sre/)

## Qué demuestra este ejemplo

El post cubre recolección de métricas, forecasting de demanda, umbrales por
zonas (verde/amarillo/naranja/rojo) y auto-escalado con HPA. Reproducir el
HPA en un cluster real no aporta nada nuevo respecto al YAML que ya está en
el post, así que este ejemplo se enfoca en la parte que sí requiere lógica y
es el corazón de la disciplina: **pasar de "tengo métricas históricas" a
"sé cuántos días me quedan antes de tener que escalar"**.

`capacity_planner.py` reimplementa, en una versión reducida pero funcional,
las clases `CapacityMetric`, `CapacityCollector` y `CapacityForecaster` del
post:

- Genera 30 días de utilización de CPU sintética con tendencia de
  crecimiento + estacionalidad diaria + ruido (semilla fija, reproducible).
- Clasifica cada hora histórica en una zona de umbral, usando los mismos
  cortes que describe el post (60/70/80/90%).
- Entrena una regresión lineal con features cíclicas (hora del día, día de
  la semana) idéntica en espíritu al `CapacityForecaster` del post, y
  proyecta 14 días hacia adelante.
- Calcula en cuántos días el forecast cruza cada umbral y emite una
  recomendación de acción si el umbral de escalado preventivo (80%) se
  cruza dentro de los próximos 7 días.

No incluye el HPA de Kubernetes ni la recolección de métricas reales vía
`psutil`/Prometheus (eso ya está documentado en el post); se enfoca en la
parte de forecasting y toma de decisión, que es donde el capacity planning
deja de ser "mirar un dashboard" y pasa a ser una práctica sistemática.

## Requisitos

- Python 3.9+
- pip

No requiere Docker, Kubernetes ni ninguna cuenta cloud.

## Cómo correrlo

```bash
cd capacity-planning-sre
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 capacity_planner.py
```

## Salida esperada

```
=== Estado actual de capacidad ===
Servicio: api-service (recurso: cpu)
Utilización actual: 68.5%
Headroom actual: 31.5%
Zona actual: verde

=== Distribución de zonas en los últimos 30 días ===
  verde    :  713 horas ( 99.0%)
  amarillo :    7 horas (  1.0%)
  naranja  :    0 horas (  0.0%)
  rojo     :    0 horas (  0.0%)

=== Forecast a 14 días (R^2 del modelo: 0.935) ===
Utilización proyectada al final del periodo: 82.4%

=== Días hasta cruzar cada umbral (según forecast) ===
  amarillo (atención)             :   0.8 días
  naranja (escalado preventivo)   :  10.9 días
  rojo (crítico)                  : no se alcanza en los próximos 14 días

OK: no se proyecta necesidad de escalado preventivo dentro de los próximos 7 días.
```

Los números exactos dependen de la fecha en que se corra el script (afecta
qué hora del día cae al final de los 30 días históricos), pero la forma de
la salida y el orden de magnitud son estables gracias a la semilla fija
(`RANDOM_SEED = 42`).

## Cómo mapea al post

| Concepto del post | En el código |
|---|---|
| `CapacityMetric` / `headroom_percent()` / `is_critical()` | `CapacityMetric.headroom_percent()` / `zone()` |
| `CapacityCollector.collect_system_metrics()` | `CapacityCollector.collect_history()` (simulado en vez de `psutil`) |
| Umbrales verde/amarillo/naranja/rojo (60/70/80/90%) | Constantes `WARNING_THRESHOLD`, `PREVENTIVE_THRESHOLD`, `CRITICAL_THRESHOLD` |
| `CapacityForecaster` con features cíclicas | `CapacityForecaster` (mismo enfoque, features recortadas) |
| "El capacity plan debe incluir la verificación y el pedido anticipado de cuotas" | Bloque final: recomendación de acción si el forecast cruza el umbral preventivo en menos de 7 días |

## Ajustar el ejemplo

- Cambiar `RANDOM_SEED` en `capacity_planner.py` simula otro servicio.
- Subir el valor de `trend` en `CapacityCollector.collect_history` simula un
  crecimiento más agresivo, para ver cómo se acorta el "días hasta crítico".
- `FORECAST_DAYS` controla el horizonte de la proyección.
