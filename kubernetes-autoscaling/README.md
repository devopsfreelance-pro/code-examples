# Kubernetes Autoscaling (HPA)

Ejemplo ejecutable del post [Guía Completa de Kubernetes autoscaling](https://www.devopsfreelance.pro/blog/posts/kubernetes-autoscaling/).

## Que demuestra

El concepto central del post: el **Horizontal Pod Autoscaler (HPA)** ajustando automaticamente el numero de replicas de un Deployment segun el uso real de CPU, sin intervencion manual.

El ejemplo levanta un cluster Kubernetes local con `kind` y despliega:

- **php-apache**: la app clasica de referencia para demos de HPA (`registry.k8s.io/hpa-example`), un servidor PHP que quema CPU calculando raices cuadradas en cada request. Se despliega con 1 replica inicial y `requests.cpu: 200m` (`deployment.yaml`).
- **metrics-server**: recolecta el uso de CPU/memoria de los pods y lo expone via la API de metricas, que es lo que el HPA consulta cada 15 segundos (como explica el post). En `kind` hace falta parchearlo para que acepte el TLS self-signed del kubelet.
- **php-apache-hpa**: un HPA v2 (`hpa.yaml`) con el mismo formato que los ejemplos del post: `minReplicas: 1`, `maxReplicas: 6`, target de 50% de CPU, y un bloque `behavior` que escala hacia arriba rapido (duplica cada 15s) y hacia abajo conservador (con `stabilizationWindowSeconds: 60` para evitar flapping).
- **load-generator**: un pod `busybox` (`load-generator.yaml`) que golpea el Service `php-apache` en loop infinito para generar la carga de CPU que dispara el escalado.

Es el mismo ciclo que describe el articulo: metrics-server mide CPU -> el HPA calcula replicas deseadas cada 15s -> el Deployment escala -> las politicas de `behavior` controlan la velocidad de subida/bajada.

## Requisitos

- [kind](https://kind.sigs.k8s.io/) (Kubernetes in Docker)
- `kubectl`
- Docker corriendo localmente

No requiere cuentas cloud ni servicios pagos: todo corre en un cluster kind local.

## Pasos para correrlo

1. Entrar al directorio y dar permisos de ejecucion al script:

```bash
cd kubernetes-autoscaling
chmod +x setup.sh
```

2. Correr el setup (crea el cluster kind, instala metrics-server, despliega la app, aplica el HPA y lanza el generador de carga):

```bash
./setup.sh
```

El script tarda unos 2-3 minutos, principalmente esperando a que `metrics-server` empiece a reportar metricas reales.

3. Observar el HPA escalando en vivo:

```bash
kubectl get hpa php-apache-hpa --watch
```

4. Cuando termines de ver el escalado hacia arriba, cortar la carga para ver el scale-down (tarda ~1 minuto por el `stabilizationWindowSeconds: 60`):

```bash
kubectl delete pod load-generator
```

5. Destruir el cluster de la demo:

```bash
kind delete cluster --name hpa-demo
```

## Salida esperada

Apenas aplicado el HPA, con el cluster recien creado y sin carga:

```
NAME             REFERENCE               TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
php-apache-hpa   Deployment/php-apache   0%/50%    1         6         1          10s
```

Con el `load-generator` corriendo, en 1-2 minutos el uso de CPU supera el 50% objetivo y el HPA empieza a crear replicas:

```
NAME             REFERENCE               TARGETS     MINPODS   MAXPODS   REPLICAS   AGE
php-apache-hpa   Deployment/php-apache   287%/50%    1         6         1          70s
php-apache-hpa   Deployment/php-apache   287%/50%    1         6         2          85s
php-apache-hpa   Deployment/php-apache   180%/50%    1         6         4          100s
php-apache-hpa   Deployment/php-apache   62%/50%     1         6         6          130s
```

Al borrar `load-generator`, TARGETS vuelve a bajar y despues de la ventana de estabilizacion de 60s el HPA reduce REPLICAS de a poco (segun la politica `scaleDown` de `hpa.yaml`) hasta volver a 1.

## Archivos

- `deployment.yaml` - Deployment + Service de la app `php-apache`.
- `hpa.yaml` - HorizontalPodAutoscaler v2 con target de CPU y politicas `behavior` de scale up/down.
- `load-generator.yaml` - Pod `busybox` que genera trafico continuo para forzar el escalado.
- `setup.sh` - Orquesta todo: crea el cluster, instala y parchea metrics-server, despliega y aplica el HPA.
