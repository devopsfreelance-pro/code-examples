# AWS vs Azure vs GCP: Calculadora de decisión ponderada

Post: [AWS vs Azure vs GCP: Comparativa de los Gigantes del Cloud Computing](https://www.devopsfreelance.pro/blog/posts/aws-vs-azure-vs-gcp--comparativa-de-los-gigantes-del-cloud-computing/)

## Qué demuestra

El post cierra con un framework de evaluación ponderada (`CloudProviderEvaluator`) para
elegir entre AWS, Azure y GCP según varios criterios (costo, performance, ecosistema,
seguridad, innovación, soporte, compliance), cada uno con un peso distinto.

Este ejemplo toma esa idea y la convierte en una herramienta CLI real:

- `config.yaml` define los pesos de cada criterio y el puntaje (1-10) de cada proveedor,
  usando los mismos valores de ejemplo del post.
- `evaluate.py` calcula el puntaje ponderado de cada proveedor, los ordena y recomienda
  el ganador. Permite sobreescribir pesos desde la línea de comandos para simular
  distintas prioridades (por ejemplo, "me importa mucho el costo y poco el soporte").

No requiere ninguna cuenta cloud ni credenciales: es puro cálculo local sobre los datos
del `config.yaml`.

## Requisitos

- Python 3.8+
- Dependencia: `pyyaml`

```bash
pip install pyyaml
```

## Cómo correrlo

1. Entrar al directorio del ejemplo:

```bash
cd aws-vs-azure-vs-gcp--comparativa-de-los-gigantes-del-cloud-computing
```

2. Ejecutar con los pesos por defecto (los del post):

```bash
python3 evaluate.py
```

Salida esperada:

```
Pesos de criterios:
  - cost        : 0.25
  - performance : 0.20
  - ecosystem   : 0.15
  - security    : 0.15
  - innovation  : 0.10
  - support     : 0.10
  - compliance  : 0.05

Puesto Proveedor Puntaje ponderado   
-------------------------------------
1      AWS       8.45                
2      Azure     8.10                
3      GCP       8.05                

Proveedor recomendado: AWS
```

3. Simular otras prioridades sobreescribiendo pesos (por ejemplo, priorizar costo e
   innovación por sobre el resto; los pesos que pases deben sumar 1.0 en total):

```bash
python3 evaluate.py \
  --weight cost=0.5 \
  --weight innovation=0.2 \
  --weight performance=0.1 \
  --weight ecosystem=0.1 \
  --weight security=0.05 \
  --weight support=0.025 \
  --weight compliance=0.025
```

Con estos pesos el ganador cambia a GCP, reflejando el análisis del post donde GCP
es la recomendación para startups y workloads de AI/ML.

4. Editar `config.yaml` para ajustar los puntajes de cada proveedor a tu propio caso
   de uso (por ejemplo, si tu equipo ya tiene experiencia fuerte en un proveedor
   particular, subile el puntaje de "ecosystem" o "support").

## Archivos

- `config.yaml` - pesos de criterios y puntajes por proveedor.
- `evaluate.py` - script CLI que calcula el ranking ponderado y recomienda un proveedor.
