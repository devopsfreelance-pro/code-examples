# AI/ML en Operaciones IT — Ejemplo Ejecutable

Post: [AI Operaciones: Transformando la Eficiencia en DevOps 2025](https://www.devopsfreelance.pro/blog/posts/ai-ml-operaciones-it/)

## Qué demuestra

El post describe el nucleo tecnico de un sistema de "AI Operations": una capa
de **procesamiento** que hace feature engineering sobre metricas crudas
(`MetricsProcessor`) y una capa de **modelado** que detecta comportamiento
anomalo con Isolation Forest (`AnomalyDetector`), ambas tomadas literalmente
de los snippets del articulo.

Este ejemplo conecta esas dos clases en un mini pipeline completo y
verificable, en lugar de dejarlas como fragmentos sueltos:

1. **Genera metricas sinteticas** de un servicio (CPU, memoria, requests/seg):
   200 muestras de comportamiento normal con ruido gaussiano + 10 muestras
   anomalas (picos de CPU/memoria con caida de trafico, simulando un
   incidente real).
2. **Procesa las metricas** con `MetricsProcessor`: calcula tendencia de CPU
   (media movil), spikes de memoria (diferencia) y cambio en tasa de
   requests, igual que en el post.
3. **Entrena `AnomalyDetector`** (Isolation Forest) solo con datos normales
   (simulando "historico sin incidentes") y lo corre sobre el dataset
   completo para detectar las anomalias inyectadas.
4. **Evalua el resultado** contra el ground truth conocido (cuantas de las
   10 anomalas inyectadas detecto el modelo).

No se incluyen las capas de ingesta (Kafka/Elasticsearch/Prometheus) ni el
tracking de experimentos con MLflow que menciona el post mas adelante,
porque requieren infraestructura externa; la parte de feature engineering +
deteccion de anomalias — el corazon tecnico y reproducible del articulo —
corre completamente en local con datos sinteticos.

## Requisitos

- Python 3.9+
- `pip` / `venv`

## Cómo correrlo

```bash
cd ai-ml-operaciones-it
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 ai_ops_pipeline.py
```

## Salida esperada

```
======================================================================
1) GENERACION DE METRICAS SINTETICAS
======================================================================
Total de muestras: 210
Anomalas inyectadas (ground truth): 10

======================================================================
2) PROCESAMIENTO DE METRICAS (MetricsProcessor)
======================================================================
   cpu_usage  memory_usage  cpu_trend  memory_spike
0  45.708238     44.146232  45.708238      0.000000
1  32.725083     53.427176  39.216660      9.280944
2  29.020802     45.558277  35.818041     -7.868899
3  34.182786     47.181307  35.409227      1.623030
4  26.585651     49.047305  33.644512      1.865998

======================================================================
3) ENTRENAMIENTO Y DETECCION (AnomalyDetector / Isolation Forest)
======================================================================
Umbral de score (percentil 90): 0.5636
Anomalias detectadas por el modelo: 20

 cpu_usage  memory_usage  requests_per_sec  anomaly_score  is_synthetic_anomaly
 85.517590     90.440673         15.074192       0.779054                  True
 90.217833     92.110816          8.564875       0.779054                  True
 97.945823     96.654883         11.020333       0.779054                  True
 ...

======================================================================
4) EVALUACION CONTRA GROUND TRUTH
======================================================================
El modelo detecto 10 de 10 anomalias inyectadas (picos de CPU/memoria con caida de trafico).
```

Los valores exactos de `anomaly_score` y las filas intermedias pueden variar
levemente segun la version de `scikit-learn`, pero el patron se mantiene:
Isolation Forest, entrenado solo con datos normales, aisla las 10 anomalas
inyectadas (CPU/memoria altos, trafico caido) con un score claramente
superior al del resto del dataset — el modelo marca ademas algunas muestras
adicionales cerca del borde de la distribucion normal (falsos positivos
esperables dado `contamination=0.05`).

## Archivos

- `ai_ops_pipeline.py` — `MetricsProcessor` + `AnomalyDetector` (Isolation
  Forest) + generador de metricas sinteticas + evaluacion contra ground
  truth.
- `requirements.txt` — dependencias: `pandas`, `scikit-learn`, `numpy`.
