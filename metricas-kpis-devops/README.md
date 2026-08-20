# Métricas y KPIs para DevOps: calculadora de DORA metrics

Ejemplo de código para el post [Guía Completa de Métricas y KPIs para DevOps](https://www.devopsfreelance.pro/blog/posts/metricas-kpis-devops/).

## Qué demuestra este ejemplo

El post explica las cuatro DORA metrics (frecuencia de despliegue, lead time
for changes, MTTR y change failure rate) con fragmentos de código sueltos.
Este ejemplo los une en un script Python ejecutable que:

1. Lee un dataset de ejemplo (`deployments.json`) con 15 despliegues y 2
   incidentes.
2. Calcula las 4 métricas DORA sobre esos datos.
3. Categoriza cada métrica según los umbrales de rendimiento de la
   investigación DORA (Elite / Alto / Medio / Bajo).
4. Imprime el resultado en JSON, listo para alimentar un dashboard o un
   reporte.

## Requisitos

- Python 3.8 o superior (solo librería estándar, sin dependencias externas).

## Cómo correrlo

```bash
cd metricas-kpis-devops
python3 dora_metrics.py deployments.json
```

## Salida esperada

```json
{
  "1_frecuencia_despliegue": {
    "despliegues_totales": 13,
    "periodo_dias": 15,
    "frecuencia_diaria": 0.87,
    "categoria": "Alto"
  },
  "2_lead_time_for_changes": {
    "lead_time_promedio_horas": 5.9,
    "lead_time_maximo_horas": 56.0,
    "categoria": "Elite"
  },
  "3_mean_time_to_recovery": {
    "mttr_promedio_minutos": 225.0,
    "incidentes_totales": 2,
    "categoria": "Alto"
  },
  "4_change_failure_rate": {
    "tasa_fallos_pct": 13.3,
    "despliegues_totales": 15,
    "despliegues_fallidos": 2,
    "categoria": "Elite/Alto"
  }
}
```

## Archivos

- `dora_metrics.py`: script que calcula las 4 métricas DORA.
- `deployments.json`: dataset de ejemplo con despliegues e incidentes
  (cada incidente puede referenciar el `deployment_id` que lo causó, tal
  como se describe en el post para calcular la change failure rate).

## Adaptarlo a datos reales

Para usarlo con tu propia infraestructura, generá un JSON con el mismo
formato a partir de tu sistema de CI/CD (GitHub Actions, GitLab CI, Jenkins)
y tu herramienta de incidentes (PagerDuty, Opsgenie, Jira). Los campos
`commit_created_at` y `deployed_at` deben venir de tus pipelines; los campos
`detected_at` / `resolved_at` de tu sistema de gestión de incidentes.
