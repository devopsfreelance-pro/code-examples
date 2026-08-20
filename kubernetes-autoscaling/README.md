# Kubernetes Autoscaling (HPA)

Runnable example from the post [Kubernetes HPA: Complete Guide to Dynamic Autoscaling](https://www.devopsfreelance.pro/blog/en/posts/kubernetes-hpa-guide/).

## What it demonstrates

The core concept of the post: the **Horizontal Pod Autoscaler (HPA)** automatically adjusting the number of replicas of a Deployment based on real CPU usage, with no manual intervention.

The example spins up a local Kubernetes cluster with `kind` and deploys:

- **php-apache**: the classic reference app for HPA demos (`registry.k8s.io/hpa-example`), a PHP server that burns CPU calculating square roots on every request. It's deployed with 1 initial replica and `requests.cpu: 200m` (`deployment.yaml`).
- **metrics-server**: collects pod CPU/memory usage and exposes it through the metrics API, which is what HPA queries every 15 seconds (as explained in the post). On `kind` it needs to be patched to accept the kubelet's self-signed TLS.
- **php-apache-hpa**: an HPA v2 (`hpa.yaml`) with the same shape as the examples in the post: `minReplicas: 1`, `maxReplicas: 6`, a 50% CPU target, and a `behavior` block that scales up fast (doubles every 15s) and scales down conservatively (with `stabilizationWindowSeconds: 60` to avoid flapping).
- **load-generator**: a `busybox` pod (`load-generator.yaml`) that hits the `php-apache` Service in an infinite loop to generate the CPU load that triggers scaling.

It's the same cycle described in the article: metrics-server measures CPU -> HPA calculates the desired replicas every 15s -> the Deployment scales -> the `behavior` policies control the speed of scale-up/scale-down.

## Requirements

- [kind](https://kind.sigs.k8s.io/) (Kubernetes in Docker)
- `kubectl`
- Docker running locally

No cloud accounts or paid services required: everything runs on a local kind cluster.

## Steps to run it

1. Enter the directory and make the script executable:

```bash
cd kubernetes-autoscaling
chmod +x setup.sh
```

2. Run the setup (creates the kind cluster, installs metrics-server, deploys the app, applies the HPA, and launches the load generator):

```bash
./setup.sh
```

The script takes about 2-3 minutes, mostly waiting for `metrics-server` to start reporting real metrics.

3. Watch the HPA scaling live:

```bash
kubectl get hpa php-apache-hpa --watch
```

4. When you're done watching it scale up, cut the load to see the scale-down (it takes ~1 minute because of `stabilizationWindowSeconds: 60`):

```bash
kubectl delete pod load-generator
```

5. Tear down the demo cluster:

```bash
kind delete cluster --name hpa-demo
```

## Expected output

Right after applying the HPA, with a freshly created cluster and no load:

```
NAME             REFERENCE               TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
php-apache-hpa   Deployment/php-apache   0%/50%    1         6         1          10s
```

With `load-generator` running, within 1-2 minutes CPU usage exceeds the 50% target and HPA starts creating replicas:

```
NAME             REFERENCE               TARGETS     MINPODS   MAXPODS   REPLICAS   AGE
php-apache-hpa   Deployment/php-apache   287%/50%    1         6         1          70s
php-apache-hpa   Deployment/php-apache   287%/50%    1         6         2          85s
php-apache-hpa   Deployment/php-apache   180%/50%    1         6         4          100s
php-apache-hpa   Deployment/php-apache   62%/50%     1         6         6          130s
```

After deleting `load-generator`, TARGETS drops back down, and after the 60s stabilization window HPA gradually reduces REPLICAS (per the `scaleDown` policy in `hpa.yaml`) until it's back to 1.

## Files

- `deployment.yaml` - Deployment + Service for the `php-apache` app.
- `hpa.yaml` - HorizontalPodAutoscaler v2 with a CPU target and scale up/down `behavior` policies.
- `load-generator.yaml` - `busybox` pod that generates continuous traffic to force scaling.
- `setup.sh` - Orchestrates everything: creates the cluster, installs and patches metrics-server, deploys the app, and applies the HPA.

---

## 🇪🇸 Versión en español

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
