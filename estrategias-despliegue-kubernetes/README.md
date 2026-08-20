# Kubernetes Deployment Strategies: runnable example

Post: [Kubernetes Deployment Strategies: Rolling, Blue-Green, Canary and A/B](https://www.devopsfreelance.pro/blog/en/posts/kubernetes-deployment-strategies/)

## What this example demonstrates

This directory implements, on a local `kind` cluster, the three core deployment
strategies from the post, all without needing a service mesh:

1. **Rolling Update** (`manifests/rolling-update.yaml`): a standard Deployment with
   `maxUnavailable: 25%` / `maxSurge: 25%`. You watch Pods get replaced gradually
   as the image is updated.
2. **Blue-Green** (`manifests/blue-green.yaml`): two Deployments (`app-blue`,
   `app-green`) with distinct HTML content and a single Service. The traffic
   switch between versions is a `kubectl patch` on the Service's selector
   (`scripts/switch-blue-green.sh`), instant and with equally fast rollback.
3. **Canary** (`manifests/canary.yaml`): two Deployments (`demo-stable` with 9
   replicas, `demo-canary` with 1) share the label `app: demo-canary` and a single
   Service. Without Istio: kube-proxy round-robins across the Pods of both
   Deployments, so the replica ratio defines the traffic ratio (~90%/10%), the
   same concept the post's Istio example illustrates, but using only native
   Kubernetes primitives.

## Requirements

- [Docker](https://docs.docker.com/get-docker/)
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
- `kubectl`

No paid accounts or services needed: everything runs on a local `kind` cluster
with public `nginx` images.

## Steps

### 0. Create the cluster

```bash
kind create cluster --name deploy-demo
kubectl cluster-info --context kind-deploy-demo
```

### 1. Rolling Update

```bash
kubectl apply -f manifests/rolling-update.yaml
kubectl rollout status deployment/demo-rolling

# En otra terminal, observar el reemplazo gradual de Pods durante la actualizacion:
kubectl get pods -l app=demo-rolling -w

# Disparar la actualizacion (cambio de imagen 1.25 -> 1.27):
kubectl set image deployment/demo-rolling web=nginx:1.27-alpine
kubectl rollout status deployment/demo-rolling
kubectl rollout history deployment/demo-rolling

# Rollback a la version anterior:
kubectl rollout undo deployment/demo-rolling
```

Expected output from `kubectl rollout status`:

```
Waiting for deployment "demo-rolling" rollout to finish: ...
deployment "demo-rolling" successfully rolled out
```

### 2. Blue-Green

```bash
kubectl apply -f manifests/blue-green.yaml
kubectl rollout status deployment/app-blue
kubectl rollout status deployment/app-green

# Verificar que el Service apunta a blue:
kubectl port-forward svc/demo-bluegreen 8080:80 &
curl -s localhost:8080
# -> <h1>BLUE - version estable (v1)</h1>

# Switch de trafico a green:
chmod +x scripts/switch-blue-green.sh
./scripts/switch-blue-green.sh green
curl -s localhost:8080
# -> <h1>GREEN - version nueva (v2)</h1>

# Rollback instantaneo si algo falla:
./scripts/switch-blue-green.sh blue

kill %1  # cerrar el port-forward
```

### 3. Canary

```bash
kubectl apply -f manifests/canary.yaml
kubectl rollout status deployment/demo-stable
kubectl rollout status deployment/demo-canary

kubectl port-forward svc/demo-canary 8081:80 &

# 20 requests para ver la proporcion real de trafico stable/canary:
for i in $(seq 1 20); do curl -s localhost:8081; echo; done | sort | uniq -c

kill %1
```

Expected output (approximate; kube-proxy round-robins across the Service's
endpoints and doesn't guarantee an exact split on small samples):

```
  18 <html><body><h1>STABLE v1</h1></body></html>
   2 <html><body><h1>CANARY v2</h1></body></html>
```

### Cleanup

```bash
kind delete cluster --name deploy-demo
```

## Notes

- The manifests use `nginx:1.25-alpine` / `nginx:1.27-alpine`, official public
  images, no credentials required.
- In production, traffic splitting by replica ratio (used in the Canary
  example) is a valid but approximate technique; for fine-grained control by
  exact percentage you'd use a service mesh (Istio, Linkerd) as shown in the
  post, or an Ingress Controller with canary support (nginx-ingress, Traefik).

---

## 🇪🇸 Versión en español

# Estrategias de Despliegue en Kubernetes: ejemplo ejecutable

Post: [Estrategias de Despliegue en Kubernetes: Rolling, Blue-Green, Canary y A/B](https://www.devopsfreelance.pro/blog/posts/estrategias-despliegue-kubernetes/)

## Qué demuestra este ejemplo

Este directorio implementa, sobre un cluster local con `kind`, las tres estrategias
de despliegue centrales del post, todas sin necesidad de un service mesh:

1. **Rolling Update** (`manifests/rolling-update.yaml`): Deployment estandar con
   `maxUnavailable: 25%` / `maxSurge: 25%`. Se observa el reemplazo gradual de Pods
   al actualizar la imagen.
2. **Blue-Green** (`manifests/blue-green.yaml`): dos Deployments (`app-blue`,
   `app-green`) con contenido HTML distinto y un unico Service. El switch de
   trafico entre versiones es un `kubectl patch` del selector del Service
   (`scripts/switch-blue-green.sh`), instantaneo y con rollback igual de rapido.
3. **Canary** (`manifests/canary.yaml`): dos Deployments (`demo-stable` con 9
   replicas, `demo-canary` con 1) comparten label `app: demo-canary` y un mismo
   Service. Sin Istio: kube-proxy balancea round-robin entre los Pods de ambos
   Deployments, asi que la proporcion de replicas define la proporcion de
   trafico (~90%/10%), el mismo concepto que ilustra el ejemplo de Istio del post
   pero usando solo primitivas nativas de Kubernetes.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/)
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
- `kubectl`

Sin cuentas ni servicios pagos: todo corre en un cluster `kind` local con
imagenes publicas de `nginx`.

## Pasos

### 0. Crear el cluster

```bash
kind create cluster --name deploy-demo
kubectl cluster-info --context kind-deploy-demo
```

### 1. Rolling Update

```bash
kubectl apply -f manifests/rolling-update.yaml
kubectl rollout status deployment/demo-rolling

# En otra terminal, observar el reemplazo gradual de Pods durante la actualizacion:
kubectl get pods -l app=demo-rolling -w

# Disparar la actualizacion (cambio de imagen 1.25 -> 1.27):
kubectl set image deployment/demo-rolling web=nginx:1.27-alpine
kubectl rollout status deployment/demo-rolling
kubectl rollout history deployment/demo-rolling

# Rollback a la version anterior:
kubectl rollout undo deployment/demo-rolling
```

Salida esperada de `kubectl rollout status`:

```
Waiting for deployment "demo-rolling" rollout to finish: ...
deployment "demo-rolling" successfully rolled out
```

### 2. Blue-Green

```bash
kubectl apply -f manifests/blue-green.yaml
kubectl rollout status deployment/app-blue
kubectl rollout status deployment/app-green

# Verificar que el Service apunta a blue:
kubectl port-forward svc/demo-bluegreen 8080:80 &
curl -s localhost:8080
# -> <h1>BLUE - version estable (v1)</h1>

# Switch de trafico a green:
chmod +x scripts/switch-blue-green.sh
./scripts/switch-blue-green.sh green
curl -s localhost:8080
# -> <h1>GREEN - version nueva (v2)</h1>

# Rollback instantaneo si algo falla:
./scripts/switch-blue-green.sh blue

kill %1  # cerrar el port-forward
```

### 3. Canary

```bash
kubectl apply -f manifests/canary.yaml
kubectl rollout status deployment/demo-stable
kubectl rollout status deployment/demo-canary

kubectl port-forward svc/demo-canary 8081:80 &

# 20 requests para ver la proporcion real de trafico stable/canary:
for i in $(seq 1 20); do curl -s localhost:8081; echo; done | sort | uniq -c

kill %1
```

Salida esperada (aproximada, kube-proxy balancea round-robin sobre los
endpoints del Service, no garantiza un split exacto en muestras chicas):

```
  18 <html><body><h1>STABLE v1</h1></body></html>
   2 <html><body><h1>CANARY v2</h1></body></html>
```

### Limpieza

```bash
kind delete cluster --name deploy-demo
```

## Notas

- Los manifiestos usan `nginx:1.25-alpine` / `nginx:1.27-alpine`, imagenes
  publicas oficiales, sin credenciales.
- En produccion, el split de trafico por proporcion de replicas (usado en el
  ejemplo de Canary) es una tecnica valida pero aproximada; para control fino
  por porcentaje exacto se usa un service mesh (Istio, Linkerd) como muestra
  el post, o un Ingress Controller con soporte de canary (nginx-ingress,
  Traefik).
