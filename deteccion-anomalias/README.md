# Deteccion de anomalias con Isolation Forest

Ejemplo ejecutable del post [Detección Anomalías: Guía Práctica para Equipos DevOps 2025](https://www.devopsfreelance.pro/blog/posts/deteccion-anomalias/).

## Que demuestra

El post explica que la detección de anomalías moderna reemplaza los umbrales
estáticos por modelos que aprenden qué es "normal" a partir de datos
históricos, usando entre otras técnicas Isolation Forest. Este ejemplo
implementa exactamente ese flujo con `scikit-learn`:

1. `generar_metricas_historicas()` simula 2000 muestras "normales" de
   latencia (ms) y uso de CPU (%) de una API, como las que en un caso real
   vendrían de Prometheus.
2. Se entrena un `IsolationForest` sobre esos datos históricos, igual que en
   el snippet del post.
3. `generar_metricas_actuales()` genera un lote de 200 muestras "actuales" e
   inyecta a propósito 8 anomalías puntuales (picos de latencia tipo
   50ms -> 5s, o saturación de CPU al 95-100%), replicando el ejemplo del
   artículo de una API que normalmente responde en 50ms.
4. El detector evalúa el lote actual con `predict()` y `score_samples()` y el
   script imprime una tabla comparando qué anomalías fueron inyectadas
   realmente contra cuáles detectó el modelo (verdaderos positivos, falsos
   negativos y falsos positivos).

Como los datos son sintéticos con semillas fijas (`random_state`/`seed`), el
resultado es reproducible: siempre detecta las 8 anomalías inyectadas más
algunos falsos positivos, mostrando en la práctica el trade-off del parámetro
`contamination` que menciona el post.

## Requisitos

- Python 3.9 o superior
- `pip` y `venv` (vienen con la instalación estándar de Python)

No requiere cuentas, servicios externos ni infraestructura: corre 100% local
con datos sintéticos generados en el propio script.

## Pasos para correrlo

```bash
cd deteccion-anomalias
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python detect_anomalies.py
```

## Salida esperada

Una tabla con las filas donde hubo anomalía inyectada y/o detectada, más un
resumen de verdaderos positivos, falsos negativos y falsos positivos. Con las
semillas fijas del script el resultado es siempre el mismo:

```
=== Deteccion de anomalias (Isolation Forest) ===
Metricas historicas usadas para entrenar: 2000
Metricas actuales evaluadas: 200
Anomalias inyectadas realmente: 8
Anomalias detectadas por el modelo: 11

idx  | latencia_ms | cpu_%  | score    | inyectada | detectada
-----|-------------|--------|----------|-----------|----------
  19 |        39.7 |   99.2 |  -0.6734 | si        | si
  26 |        29.9 |   25.1 |  -0.6225 | no        | si
  49 |        66.0 |   15.3 |  -0.6474 | no        | si
  50 |        56.1 |    2.5 |  -0.6335 | no        | si
  55 |       634.8 |   25.6 |  -0.6708 | si        | si
  84 |        48.4 |   95.3 |  -0.6647 | si        | si
  91 |        55.3 |   98.7 |  -0.6602 | si        | si
 115 |       660.2 |   36.1 |  -0.6634 | si        | si
 140 |        58.8 |   97.3 |  -0.6621 | si        | si
 155 |       575.8 |   38.0 |  -0.6551 | si        | si
 158 |        63.2 |   95.1 |  -0.6762 | si        | si

Verdaderos positivos: 8
Falsos negativos:     0
Falsos positivos:     3
```

Las filas con `inyectada = si` y `detectada = si` son las anomalías reales
que el modelo encontró (picos de latencia >300ms o CPU >90%). Las filas con
`inyectada = no` y `detectada = si` son falsos positivos: puntos dentro de
rango normal que el modelo marcó igual como raros, algo esperable con
`contamination=0.04` tal como advierte el post sobre ajustar ese parámetro
según la tasa de anomalías real de cada entorno.

## Ir mas alla

- Cambiar `contamination` en `detect_anomalies.py` (por ejemplo a `0.01`) y
  ver cómo baja la cantidad de falsos positivos a costa de arriesgar más
  falsos negativos.
- Reemplazar `generar_metricas_actuales()` por datos reales exportados desde
  Prometheus (por ejemplo con la HTTP API `/api/v1/query_range`) para probar
  el detector contra métricas de un sistema real.
