# MLOps DevOps: despliegue canary de modelos en minutos

Ejemplo de código para el post [MLOps DevOps: Guía completa para equipos modernos 2026](https://www.devopsfreelance.pro/blog/posts/devops-aplicaciones-machine-learning/).

## Qué demuestra

El post describe tres pilares de MLOps: ml pipelines, feature store y model
deployment. Este ejemplo se enfoca en el pilar de **model deployment con
estrategia canary**, la técnica que el post menciona como forma de minimizar
riesgos al llevar un modelo nuevo a producción.

Se levantan tres servicios con Docker Compose:

- `model-v1`: el modelo "estable", ya validado en producción (precisión
  simulada del 85%).
- `model-v2`: el modelo "candidato" o canary, con mejor precisión simulada
  (93%), que representa una nueva versión recién entrenada.
- `router`: un proxy de inferencia que distribuye el tráfico entre v1 y v2
  según un porcentaje configurable (`CANARY_WEIGHT`, 10% por defecto) y
  expone un endpoint `/metrics` con la tasa de predicciones positivas por
  versión, la señal mínima que un pipeline de CI/CD usaría para decidir si
  promueve el canary a estable o revierte el despliegue.

## Requisitos

- Docker y Docker Compose (`docker compose version` >= 2.x)
- `curl` para probar los endpoints

No requiere cuentas ni credenciales de ningún proveedor cloud: todo corre
localmente en contenedores.

## Cómo correrlo

1. Levantar los tres servicios:

```bash
cd devops-aplicaciones-machine-learning
docker compose up --build
```

2. En otra terminal, enviar varias peticiones de inferencia al router
   (simula tráfico real de la aplicación que consume el modelo):

```bash
for i in $(seq 1 50); do
  curl -s -X POST http://localhost:8080/predict \
    -H "Content-Type: application/json" \
    -d '{"features": [0.12, 0.98, 0.33]}'
  echo
done
```

Cada respuesta indica qué versión del modelo atendió la petición (`routed_to`)
y su predicción. Con `CANARY_WEIGHT=10`, aproximadamente el 10% de las
peticiones deberían ir a `v2`.

3. Consultar las métricas acumuladas por versión, la información que un
   pipeline usaría para decidir si promueve el canary:

```bash
curl -s http://localhost:8080/metrics | python3 -m json.tool
```

Salida esperada (los valores exactos varían por la aleatoriedad simulada):

```json
{
  "canary_weight": 10.0,
  "metrics": {
    "v1": {
      "requests": 45,
      "positive_rate": 0.822
    },
    "v2": {
      "requests": 5,
      "positive_rate": 0.9
    }
  }
}
```

4. Para simular una "promoción" del canary (v2 pasa a recibir el 100% del
   tráfico, como en un despliegue blue-green), editar `CANARY_WEIGHT` en
   `docker-compose.yml` a `100` y volver a levantar el router:

```bash
docker compose up -d --build router
```

5. Apagar todo:

```bash
docker compose down
```

## Estructura

```
devops-aplicaciones-machine-learning/
├── docker-compose.yml   # Orquesta model-v1, model-v2 y el router
├── Dockerfile            # Imagen compartida (Flask) para las 3 apps
├── model_service.py      # Servicio de inferencia (una version del modelo)
└── router.py              # Router canary + endpoint de metricas
```

## Notas

- Los modelos y las métricas de precisión están simulados con
  `random.random()`; el objetivo es ilustrar el mecanismo de enrutamiento y
  observación del canary, no un modelo de ML real.
- En un pipeline de CI/CD real, el paso de "promoción" (subir
  `CANARY_WEIGHT` a 100 o hacer el switch blue-green) se automatizaría
  consultando `/metrics` y comparando `positive_rate` de v2 contra v1 antes
  de continuar, cortando el pipeline si el candidato degrada el rendimiento.
