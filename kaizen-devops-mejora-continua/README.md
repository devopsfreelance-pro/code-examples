# Kaizen DevOps: medir el impacto de una mejora con metricas DORA

Ejemplo de codigo que acompaña al post [Kaizen DevOps: Guía completa de mejora continua 2026](https://www.devopsfreelance.pro/blog/posts/kaizen-devops-mejora-continua/).

## Que demuestra

El post describe el ciclo kaizen devops como "se formula una hipotesis de
mejora, se implementa un cambio pequeño, se mide el resultado con metricas
objetivas y se decide si consolidar o revertir la modificacion", usando las
4 metricas DORA (deployment frequency, lead time for changes, time to
restore service y change failure rate) como vara de medicion.

Este ejemplo implementa exactamente ese ciclo con datos sinteticos de dos
sprints consecutivos de un mismo equipo:

- `deployments_sample.json`: despliegues e incidentes del **sprint 12**
  (antes de la retrospectiva) y del **sprint 13** (despues de aplicar las
  acciones kaizen decididas: lotes de cambio mas chicos y mas frecuentes,
  reviews mas agiles, un incidente resuelto con feature flag en vez de
  rollback manual).
- `dora_metrics.py`: calcula las 4 metricas DORA para cada sprint, las
  clasifica segun los niveles de referencia (Elite / High / Medium / Low)
  y muestra la variacion entre sprints para responder la pregunta central
  de una retrospectiva kaizen: **¿la mejora que aplicamos tuvo impacto
  medible?**

No incluye el resto de practicas culturales del post (retrospectivas en
vivo, kaizen boards, blameless postmortems, asignacion de tiempo protegido):
son practicas de proceso y cultura de equipo, no algo que tenga sentido
simular en un script.

## Requisitos

- Python 3.9 o superior (solo libreria estandar, sin `pip install`)

## Pasos para correrlo

```bash
cd kaizen-devops-mejora-continua
python3 dora_metrics.py deployments_sample.json
```

## Salida esperada

```
=== Sprint 12 (antes de aplicar mejoras kaizen) ===
  Deployment frequency : 0.29 despliegues/dia  -> High (semanal a mensual)
  Lead time for changes: 39.9 horas  -> High (un dia a una semana)
  Time to restore      : 4.25 horas  -> High (menos de un dia)
  Change failure rate  : 25.0%  -> Medium (16-30%)

=== Sprint 13 (despues de aplicar mejoras kaizen) ===
  Deployment frequency : 0.50 despliegues/dia  -> High (semanal a mensual)
  Lead time for changes: 5.4 horas  -> Elite (menos de un dia)
  Time to restore      : 0.42 horas  -> Elite (menos de una hora)
  Change failure rate  : 14.3%  -> Elite/High (0-15%)

=== Variacion sprint 1 -> sprint 2 (efecto de las mejoras kaizen) ===
  Deployment frequency : +0.21 despliegues/dia
  Lead time for changes: -34.5 horas
  Time to restore      : -3.83 horas
  Change failure rate  : -10.7 puntos porcentuales

  4/4 metricas DORA mejoraron respecto al sprint anterior.
  Veredicto kaizen: las acciones definidas en la retrospectiva
  tuvieron impacto medible. Se consolidan y se busca la siguiente mejora.
```

## Adaptarlo a datos reales

Para usarlo con datos reales de tu equipo, reemplaza
`deployments_sample.json` por deployments/incidentes exportados de tu
sistema de CI/CD y tu herramienta de incidentes (por ejemplo, tags de
despliegue en git mas eventos de PagerDuty/Opsgenie), respetando la
misma estructura de campos (`commit_at`, `deployed_at`, `started_at`,
`resolved_at`, `caused_by_deployment`).
