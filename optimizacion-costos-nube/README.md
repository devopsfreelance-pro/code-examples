# Rightsizing advisor: recomendaciones de dimensionamiento + comparativa On-Demand/Reserved/Spot

Ejemplo de código para el post [Optimizar costos cloud: Guía práctica para reducir gastos](https://www.devopsfreelance.pro/blog/posts/optimizacion-costos-nube/).

## Qué demuestra este ejemplo

El post describe tres estrategias centrales de reducción de costos: **rightsizing**
(dimensionar instancias según su uso real de CPU), **instancias reservadas /
Savings Plans** y **instancias spot**. Este ejemplo las combina en un único
script que corre en local, sin cuenta de AWS:

- `rightsizing_advisor.py` lee métricas de utilización de CPU (con el mismo
  formato que devolvería `CloudWatch GetMetricStatistics`), calcula el
  promedio y el máximo por instancia, y aplica la misma lógica de
  recomendación del post (`DOWNSIZE` / `UPSIZE` / `MANTENER` según umbrales de
  CPU promedio y máximo).
- Para las instancias marcadas como `DOWNSIZE` o `UPSIZE`, sugiere el
  siguiente tamaño de la misma familia de instancia y muestra el costo
  mensual proyectado bajo tres modelos de compra: On-Demand, Reserved
  Instance (1 año) e Instancia Spot, usando la tabla de precios de
  `pricing_table.json`.
- Para las instancias que ya están bien dimensionadas, muestra igual el
  ahorro potencial de pasarlas a Reserved o Spot sin cambiar de tamaño.
- Al final imprime un resumen con el ahorro mensual estimado solo por
  downsizing y el porcentaje de reducción sobre el costo total On-Demand.

## Requisitos

- Python 3.8+ (solo librería estándar: `csv`, `json`, `argparse`,
  `statistics`). No hace falta `pip install` ni cuenta de AWS.

## Cómo correrlo

```bash
cd optimizacion-costos-nube
python3 rightsizing_advisor.py sample_cpu_metrics.csv pricing_table.json
```

Opcional, ajustar los umbrales de decisión (los defaults son los mismos que
usa el ejemplo de boto3 del post: promedio < 20% y máximo < 50% → downsize;
promedio > 70% → upsize):

```bash
python3 rightsizing_advisor.py sample_cpu_metrics.csv pricing_table.json \
  --low-threshold 20 --low-max-threshold 50 --high-threshold 70
```

## Salida esperada

```
========================================================================
RIGHTSIZING ADVISOR - analisis de utilizacion de CPU
========================================================================

i-0a1b2c3d4e5f60001  [t3.xlarge]
  CPU promedio: 7.94%  |  CPU maximo: 14.65%  (56 muestras)
  Recomendacion: DOWNSIZE
  Costo On-Demand actual: USD 121.47/mes
  Tipo sugerido: t3.large
    On-Demand: USD 60.74/mes  (delta: +60.73 USD/mes)
    Reserved 1yr: USD 38.32/mes
    Spot (promedio): USD 18.25/mes

...

========================================================================
RESUMEN
========================================================================
Costo On-Demand actual (todas las instancias): USD 438.44/mes
Costo On-Demand tras aplicar recomendaciones:   USD 409.39/mes
Ahorro estimado solo por downsizing:            USD 91.1/mes
Reduccion neta proyectada sobre el total:       6.6%
```

(La salida completa incluye el detalle de las 5 instancias del dataset de
ejemplo: dos sobredimensionadas, una infradimensionada y dos con uso estable.)

## Archivos

- `rightsizing_advisor.py`: script principal, sin dependencias externas.
- `sample_cpu_metrics.csv`: métricas sintéticas de CPU para 5 instancias
  (`t3.xlarge`, `c5.large`, `m5.large`, `t3.large`, `c5.xlarge`) con muestras
  cada 6 horas durante 14 días, con perfiles de uso intencionalmente
  distintos (bajo, alto, estable, con picos).
- `pricing_table.json`: tabla de precios de referencia por hora
  (On-Demand, Reserved 1 año, Spot promedio) para las familias `t3`, `c5` y
  `m5`, más la "escalera de tamaños" que usa el script para sugerir el
  siguiente tipo de instancia.

## Notas

- Los precios de `pricing_table.json` son valores de referencia para el
  ejemplo, no una cotización oficial de AWS. Para usar el script con datos
  reales, exportá las métricas con `aws cloudwatch get-metric-statistics`
  (mismo enfoque que el snippet de boto3 del post) al formato CSV de
  `sample_cpu_metrics.csv`, y actualizá `pricing_table.json` con los precios
  vigentes de tu región (`aws pricing get-products` o la calculadora de AWS).
- No se incluyen credenciales ni cuentas de AWS: todo corre en local con
  datos de muestra.
