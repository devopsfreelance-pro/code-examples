# Green IT y sostenibilidad en DevOps - Calculadora de huella de carbono

Post del blog: https://www.devopsfreelance.pro/blog/posts/green-it-sostenibilidad-devops/

## Que demuestra este ejemplo

El post explica que uno de los pilares del DevOps sostenible es la **medicion
continua**: no se puede reducir la huella de carbono de la infraestructura si
no se sabe cuanto CO2 emite cada instancia y cuales estan subutilizadas.

Este ejemplo es una version ejecutable y sin cuenta de AWS del script de
`boto3`/CloudWatch del post. En lugar de consultar metricas en vivo, lee un
CSV con datos de uso de instancias EC2 y aplica la misma logica:

- Detecta instancias con **CPU promedio menor al 20%** (umbral de
  subutilizacion del post).
- Calcula la **huella de carbono actual** de cada instancia usando el mismo
  factor de emision (0.5 kg CO2/kWh) y las mismas estimaciones de consumo por
  tipo de instancia (t3.medium, t3.large, m5.large, m5.xlarge).
- Estima el **ahorro de CO2** si se hace rightsizing (downsizing) de esas
  instancias.
- Imprime un reporte tabular con el ahorro total estimado por mes.

## Requisitos

- Python 3.9 o superior (usa solo la libreria estandar, sin dependencias
  externas ni `boto3`).

## Como correrlo

```bash
cd green-it-sostenibilidad-devops
python3 carbon_calculator.py --csv sample_instances.csv
```

`sample_instances.csv` trae 8 instancias de ejemplo con distintos niveles de
uso de CPU para que el reporte muestre casos subutilizados y casos normales.

Para probarlo con tus propios datos, crea un CSV con las mismas columnas
(`instance_id,instance_type,cpu_promedio_pct,horas_encendida_mes`) y pasa la
ruta con `--csv`.

## Salida esperada

```
instance_id           tipo           cpu_%   ahorro_kgCO2
---------------------------------------------------------
i-0a1b2c3d4e5f60001   m5.xlarge        8.5           29.2
i-0a1b2c3d4e5f60002   m5.large        15.2           14.6
i-0a1b2c3d4e5f60003   t3.large         6.1           9.12
i-0a1b2c3d4e5f60006   t3.large        18.9            5.0
i-0a1b2c3d4e5f60008   t3.medium        3.2           4.56
---------------------------------------------------------
Instancias subutilizadas detectadas: 5
Ahorro estimado total: 62.48 kg CO2/mes
```

Las instancias `i-...0004` (t3.medium al 45%) y `i-...0005`/`i-...0007`
(m5.large al 72.3% y m5.xlarge al 55.4%) no aparecen en el reporte porque su
CPU promedio esta por encima del umbral de subutilizacion (20%): estan
correctamente dimensionadas segun el criterio del post.

## Llevarlo a produccion

En un entorno real, `analizar_instancias()` se reemplaza por una consulta a
`boto3` + CloudWatch (tal como muestra el post), manteniendo el mismo umbral,
factor de emision y logica de reporte. Este ejemplo separa esa logica del
acceso a AWS justamente para poder probarla en minutos sin credenciales ni
costos de nube.
