# Rightsizing de Recursos Cloud - Ejemplo Ejecutable

Post: [Rightsizing de Recursos Cloud: Guía Completa para Reducir Costos](https://www.devopsfreelance.pro/blog/posts/rightsizing-recursos-cloud/)

## Qué demuestra este ejemplo

El post explica que la decisión de rightsizing debe tomarse con **percentiles**, no con
promedios, y siguiendo reglas explícitas acordadas de antemano (ver sección "Decidir con
reglas explícitas" del post):

- p99 de CPU < 40% y p99 de memoria < 50% durante la ventana de medición → candidato a
  bajar un tamaño de instancia.
- Utilización nula o testimonial (CPU p99 < 3%) → candidato a apagado, no a rightsizing.
- El resto → el uso real justifica el tamaño actual, se mantiene.

`rightsizing_analyzer.py` implementa exactamente esas reglas: toma una serie de muestras
de utilización de CPU y memoria por recurso (simulando lo que devolvería CloudWatch,
Prometheus o metrics-server), calcula el promedio y el percentil 99 de cada métrica, y
emite un veredicto por recurso. `sample_metrics.csv` trae datos sintéticos de tres
recursos que ilustran los tres casos posibles:

- `web-api-prod`: CPU y memoria bajas todo el tiempo → **BAJAR UN TAMAÑO**.
- `staging-worker-02`: prácticamente sin uso → **APAGAR (ocioso)**.
- `checkout-service`: picos legítimos de CPU/memoria → **MANTENER**.

## Requisitos

- Python 3.9 o superior (no requiere librerías externas, solo la librería estándar).

## Cómo correrlo

```bash
cd rightsizing-recursos-cloud
python3 rightsizing_analyzer.py sample_metrics.csv
```

Si no se pasa argumento, usa `sample_metrics.csv` por defecto:

```bash
python3 rightsizing_analyzer.py
```

## Salida esperada

```
recurso               cpu_avg  cpu_p99  mem_avg  mem_p99  muestras   veredicto
------------------------------------------------------------------------------
checkout-service        44.8%    90.8%    56.0%    77.9%        48   MANTENER (uso justifica el tamano actual)
staging-worker-02        1.3%     2.9%     4.0%     7.0%        48   APAGAR (ocioso)
web-api-prod            13.2%    36.6%    28.2%    37.8%        48   BAJAR UN TAMANO (rightsizing)
```

## Usar con tus propios datos

El script acepta cualquier CSV con columnas `resource_id,cpu_pct,mem_pct`, una fila por
muestra (por ejemplo, una lectura horaria durante 14 días, como recomienda el post). Para
generar ese CSV a partir de CloudWatch, se puede adaptar el comando de `aws cloudwatch
get-metric-statistics` del post (sustituyendo `i-0abc123def456` por el ID real de la
instancia a analizar) y volcar los resultados a filas `resource_id,cpu_pct,mem_pct`. En
Kubernetes, la misma lógica aplica sobre datos de `metrics-server` o Prometheus por pod.

## Ajustar los umbrales

Las constantes `CPU_DOWNSIZE_THRESHOLD`, `MEM_DOWNSIZE_THRESHOLD` e
`IDLE_CPU_THRESHOLD` al inicio de `rightsizing_analyzer.py` son el punto de partida
razonable que menciona el post. En un caso real se acuerdan con los equipos dueños de
cada servicio, no se dejan como criterio individual.
