# Automatización con IA en DevOps — Ejemplo Ejecutable

Post: [IA en DevOps: Automatización Inteligente para 2025](https://www.devopsfreelance.pro/blog/posts/automatizacion-con-ia-devops/)

## Qué demuestra

El post describe dos componentes centrales de un sistema de "AI DevOps":

1. **Capa de normalización de datos**: logs de distintos servicios llegan en
   formatos distintos (timestamps, niveles de severidad) y hay que unificarlos
   antes de poder analizarlos.
2. **Motor de análisis predictivo**: el post da un ejemplo concreto de
   heurística predictiva — *"cuando el uso de CPU supera el 75% durante más de
   10 minutos, combinado con un aumento del 30% en latencia de base de datos,
   existe un 85% de probabilidad de fallo del servicio en los próximos 15
   minutos"*.

Este ejemplo implementa ambos componentes en Python puro (sin API keys, sin
servicios externos) y los conecta en un mini pipeline:

- `devops_ai_pipeline.py` normaliza logs de ejemplo con formatos de fecha
  mixtos (`DevOpsDataNormalizer`, calcado del snippet del post).
- Analiza una serie temporal de métricas (`PredictiveFailureEngine`) aplicando
  la heurística CPU + latencia del post para detectar el punto donde se
  dispara la predicción de fallo.
- Correlaciona esa predicción con los logs de error ya normalizados del mismo
  servicio, para mostrar cómo el análisis predictivo anticipa lo que después
  aparece como error en los logs.

No se incluye la parte de generación de infraestructura vía LLM (`openai`)
del post porque requiere una API key paga; la lógica de normalización y
predicción — el corazón técnico del artículo — no depende de ningún servicio
externo y corre completamente en local.

## Requisitos

- Python 3.9+
- `pip` / `venv`

## Cómo correrlo

```bash
cd automatizacion-con-ia-devops
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 devops_ai_pipeline.py
```

## Salida esperada

```
======================================================================
1) NORMALIZACION DE LOGS
======================================================================
Logs crudos: 12 (formatos de timestamp mixtos)
Logs normalizados: 12
          timestamp severity       service                              message
2026-08-19 10:00:01     info  checkout-api           request completed in 120ms
...
2026-08-19 10:01:03 critical inventory-api service unresponsive, restarting pod

======================================================================
2) MOTOR DE ANALISIS PREDICTIVO
======================================================================
Se detectaron 5 puntos en la ventana con condicion de riesgo.
Primer punto donde se dispara la prediccion:
  seconds_offset: 560
  service: inventory-api
  cpu_pct: 77.3
  latency_ms: 122.6
  latency_increase_pct: 65.3
  failure_probability: 0.85

======================================================================
3) CORRELACION CON LOGS DE ERROR (mismo servicio)
======================================================================
          timestamp severity       service                              message
2026-08-19 10:00:44    error inventory-api             connection refused by db
2026-08-19 10:01:03 critical inventory-api service unresponsive, restarting pod

CONCLUSION: el motor predictivo marco a 'inventory-api' con 85% de probabilidad de fallo
(77.3% CPU, +65.3% latencia) y los logs confirman 2 eventos error/critical en ese mismo
servicio: el patron descripto en el post se reproduce con datos locales.
```

Los valores numéricos exactos de la sección 2 pueden variar levemente porque
`sample_metrics.csv` incluye ruido aleatorio, pero el patrón (CPU > 75% +
latencia +30% → alerta predictiva, seguida de errores reales en los logs del
mismo servicio) es siempre el mismo.

## Archivos

- `devops_ai_pipeline.py` — normalizador de logs + motor predictivo + correlación.
- `sample_logs.json` — logs de ejemplo con formatos de timestamp mixtos.
- `sample_metrics.csv` — serie temporal de CPU/latencia de `inventory-api`
  (60 muestras, degradación simulada en la segunda mitad).
- `requirements.txt` — única dependencia: `pandas`.
