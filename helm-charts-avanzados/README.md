# Helm charts avanzados: helpers, labels y values por ambiente

Post relacionado: [Helm Charts Avanzados: Guía Definitiva para DevOps 2025](https://www.devopsfreelance.pro/blog/posts/helm-charts-avanzados/)

## Qué demuestra este ejemplo

Un chart mínimo (`chart/`) que ilustra el patrón central del post: **named
templates en `_helpers.tpl`** para no duplicar labels y selectors entre
`deployment.yaml` y `service.yaml`, y **un `values.yaml` base con defaults
seguros** que un archivo `values-prod.yaml` (diff mínimo) sobrescribe para
producción, tal como se describe en la sección "Gestión de valores por
ambiente" del post.

Con `helm template` se puede ver el YAML final renderizado sin necesidad de
un cluster de Kubernetes: sirve para entender exactamente qué hace `include`
con los helpers y cómo el `-f` del último archivo gana en caso de conflicto.

Archivos del chart:

- `chart/Chart.yaml` — metadata del chart.
- `chart/values.yaml` — defaults (ambiente `development`, 1 réplica).
- `chart/templates/_helpers.tpl` — `mychart.fullname`, `mychart.labels` y
  `mychart.selectorLabels`, reutilizados vía `include ... | nindent`.
- `chart/templates/deployment.yaml` — usa los helpers para labels y selector.
- `chart/templates/service.yaml` — usa el mismo `selectorLabels`, así el
  Service nunca queda desalineado del Deployment.

## Requisitos

- Helm 3 (`helm version`). Si no lo tenés instalado, usá la alternativa con
  Docker que se indica en el paso 1.
- No hace falta un cluster de Kubernetes para los pasos 1 a 3 (`lint` y
  `template` renderizan localmente). El paso 4 (deploy real) es opcional y
  requiere `kind` + `kubectl`.

## Pasos para correrlo

### 1. Clonar y pararse en este directorio

```bash
cd helm-charts-avanzados
```

Si no tenés `helm` instalado localmente, corré todos los comandos de abajo
con este wrapper de Docker (reemplazá `helm` por `docker run --rm -v
"$PWD/chart:/chart" -w / alpine/helm:3.16.3` en cada comando):

```bash
docker run --rm -v "$PWD/chart:/chart" alpine/helm:3.16.3 version
```

### 2. Lint del chart

```bash
helm lint chart/
```

Salida esperada:

```
==> Linting chart/
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### 3. Renderizar con values de desarrollo y de producción

Primero creá el archivo de diffs de producción (así se ve el patrón "diff
mínimo" del post sin necesitar un sexto archivo en el repo):

```bash
cat > chart/values-prod.yaml <<'EOF'
environment: production
replicaCount: 3
resources:
  requests:
    cpu: 250m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 256Mi
EOF
```

Renderizar con los defaults (desarrollo):

```bash
helm template myapp chart/
```

Renderizar con el override de producción, igual que en un pipeline real:

```bash
helm template myapp chart/ -f chart/values-prod.yaml --set image.tag=1.28
```

Salida esperada (fragmento del Deployment con producción aplicada):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-mychart
  labels:
    app.kubernetes.io/name: mychart
    app.kubernetes.io/instance: myapp
    app.kubernetes.io/version: "1.0.0"
    helm.sh/chart: mychart-0.1.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: mychart
      app.kubernetes.io/instance: myapp
  template:
    metadata:
      labels:
        app.kubernetes.io/name: mychart
        app.kubernetes.io/instance: myapp
        app.kubernetes.io/version: "1.0.0"
        helm.sh/chart: mychart-0.1.0
    spec:
      containers:
        - name: mychart
          image: "nginx:1.28"
          imagePullPolicy: IfNotPresent
          env:
            - name: ENVIRONMENT
              value: "production"
          resources:
            limits:
              cpu: 500m
              memory: 256Mi
            requests:
              cpu: 250m
              memory: 128Mi
          ports:
            - containerPort: 80
```

Notá `replicas: 3`, `ENVIRONMENT=production` y los resources de
`values-prod.yaml`: eso es lo que hace `include "mychart.labels"` y el
merge de `-f` en la práctica.

### 4. (Opcional) Deploy real en un cluster local con kind

Si además querés ver el release instalado de verdad:

```bash
# Requiere kind (https://kind.sigs.k8s.io/) y kubectl
kind create cluster --name helm-demo

helm upgrade --install myapp chart/ \
  -f chart/values-prod.yaml \
  --set image.tag=1.28 \
  --atomic --timeout 2m

kubectl get deployment,svc -l app.kubernetes.io/instance=myapp

kind delete cluster --name helm-demo
```

Salida esperada del `kubectl get`:

```
NAME                            READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/myapp-mychart   3/3     3            3           10s

NAME                     TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
service/myapp-mychart    ClusterIP   10.96.xx.xx    <none>        80/TCP    10s
```

## Notas

- `values-prod.yaml` no se versiona en este repo a propósito: se genera en
  el paso 3 para que el ejemplo se quede fiel al patrón "diff mínimo sobre
  el values base" que describe el post, sin duplicar todo el `values.yaml`.
- Los nombres de imagen (`nginx`) y el cluster `kind` son de ejemplo; no hay
  cuentas ni secretos involucrados.
