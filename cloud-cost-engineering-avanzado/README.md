# Cloud Cost Engineering Avanzado: mini ejemplo ejecutable

Post relacionado: [Cloud Cost Engineering Avanzado: Optimización Financiera en la Nube](https://www.devopsfreelance.pro/blog/posts/cloud-cost-engineering-avanzado/)

## Qué demuestra este ejemplo

El post describe tres capas del cloud cost engineering (visibilidad
granular, cost anomaly detection y commitment management) e incluye dos
snippets conceptuales en Python: uno de detección de anomalías con
`IsolationForest` y otro de ingesta de datos vía `boto3`/Cost Explorer.
Reproducir la ingesta real de AWS no aporta nada (requiere una cuenta y
credenciales), así que este ejemplo se enfoca en el corazón técnico del
post: **pasar de datos de costo diario a una lista concreta de anomalías
detectadas, sin depender de ninguna cuenta cloud**.

`cost_anomaly_detector.py` reimplementa, en versión reducida pero
funcional, el flujo que describe el post:

- Genera 60 días de costo diario sintético para un servicio (semilla fija,
  reproducible), con tendencia leve, estacionalidad semanal y ruido, e
  inyecta una anomalía real: un pico de ~500 USD/día a 5000 USD/día, el
  mismo ejemplo textual que usa el post ("si un servicio que normalmente
  consume 500 dólares diarios súbitamente genera un gasto de 5,000
  dólares, el sistema debe alertar").
- Ejecuta el mismo `IsolationForest` que el snippet `detect_cost_anomalies`
  del post sobre `daily_cost`, `resource_count` y `cpu_hours`.
- Ejecuta además la segunda técnica que el post menciona como
  complementaria: un análisis de desviación estándar (z-score) sobre la
  línea base histórica, útil para explicar de forma simple por qué algo
  fue marcado.
- Imprime ambos resultados para poder comparar qué detecta cada técnica.

No incluye el `commitment management` (Reserved Instances / Savings
Plans) ni la ingesta real vía AWS Cost Explorer: esas partes ya están
documentadas en el post y requieren una cuenta AWS con facturación activa.

## Requisitos

- Python 3.9+
- pip

No requiere Docker, Kubernetes ni ninguna cuenta cloud.

## Pasos para correrlo

```bash
cd cloud-cost-engineering-avanzado
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 cost_anomaly_detector.py
```

## Salida esperada

Las fechas concretas y algunos valores intermedios varían según cuándo
corras el script (el rango de 60 días se calcula desde "hoy"), pero la
estructura y la anomalía inyectada en el día 45 (~5000 USD) siempre
aparecen:

```
Dataset generado: 60 dias, costo diario promedio $597.79

Isolation Forest detecto 6 anomalia(s):
      date  daily_cost  resource_count  cpu_hours
2026-06-26  427.902960            26.0  77.143920
2026-06-27  412.339668            26.0  75.232371
2026-07-22  632.375848            24.0 121.357682
2026-07-28  568.467982            31.0 121.010111
2026-08-06 5000.000000            18.0 107.323847
2026-08-18  622.927490            20.0 123.881543

Z-score (umbral 3.0) detecto 1 anomalia(s):
      date  daily_cost  z_score
2026-08-06      5000.0 7.589668
```

`IsolationForest` con `contamination=0.1` marca también variaciones
normales (el 10% del dataset, por diseño del algoritmo), mientras que el
z-score aísla de forma limpia únicamente la anomalía real inyectada. Esto
ilustra por qué el post recomienda combinar ambas técnicas: el modelo de
ML captura patrones multivariados más sutiles, y el z-score da una
explicación simple y auditable de por qué algo se marcó como anómalo.
