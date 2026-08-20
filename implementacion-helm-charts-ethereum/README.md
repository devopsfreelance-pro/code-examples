# Mini Helm chart para un "nodo Ethereum"

Post: [Guía Completa de Implementación de Helm Charts para Ethereum](https://www.devopsfreelance.pro/blog/posts/implementacion-helm-charts-ethereum/)

## Qué demuestra

El post explica el patrón central para desplegar nodos Ethereum en Kubernetes
con Helm: un chart parametrizable (`values.yaml`) que se personaliza por
entorno con un archivo de override (`ethereum-mainnet-values.yaml` en el
post), configurando imagen, `resources` y `persistence` sin tocar el chart
base.

Este ejemplo reproduce exactamente ese flujo con un chart mínimo y real:

- `chart/` — un Helm chart con `Deployment` + `Service` + `PersistentVolumeClaim`,
  parametrizado por `network`, `syncMode`, `resources` y `persistence`, igual
  que un chart de geth/besu.
- `demo-values.yaml` — archivo de override (equivalente al
  `ethereum-mainnet-values.yaml` del post) que cambia red, recursos y tamaño
  de almacenamiento sin modificar el chart.

Para que el ejemplo corra en minutos y sin descargar 2TB de blockchain real,
el contenedor usa `hashicorp/http-echo` en vez de `ethereum/client-go`: expone
un endpoint HTTP en el puerto 8545 (el puerto RPC estándar de Ethereum) que
responde con la red y el `syncMode` configurados. La estructura del chart
(imagen, puertos, resources, persistence, service) es la misma que usarías
para un nodo real; solo cambia qué imagen corre adentro.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/)
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) (Kubernetes en Docker)
- [kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl)
- [Helm 3.8+](https://helm.sh/docs/intro/install/)

No se necesita ninguna cuenta ni servicio pago: todo corre en un cluster
local de kind.

## Pasos para correrlo

### 1. Crear el cluster local

```bash
kind create cluster --name eth-demo
kubectl cluster-info --context kind-eth-demo
```

kind trae por defecto el StorageClass `standard` (local-path-provisioner),
que es la que usa este chart para el PVC.

### 2. Instalar el chart con los valores por defecto

```bash
helm install mini-eth ./chart
kubectl get pods,pvc,svc
```

Deberías ver el pod `mini-eth-node-...` en estado `Running`, un PVC `Bound`
de 1Gi y un Service `mini-eth-node` en el puerto 8545.

### 3. Probar el endpoint RPC simulado

```bash
kubectl port-forward svc/mini-eth-node 8545:8545 &
sleep 2
curl -s http://localhost:8545
```

Salida esperada:

```
network=sepolia-demo syncMode=snap
```

Detené el port-forward con `kill %1` (o `Ctrl+C` si lo corriste en foreground).

### 4. Aplicar el override de "producción" (demo-values.yaml)

Sin modificar el chart, se cambia la red, el syncMode, los recursos y el
tamaño de almacenamiento pasando un archivo de valores, igual que en el post:

```bash
helm upgrade mini-eth ./chart -f demo-values.yaml
kubectl rollout status deployment/mini-eth-node
kubectl get pvc
```

El PVC nuevo (`mini-eth-chaindata`) debe mostrar `2Gi`. Repetir el
port-forward y el `curl` del paso 3 ahora devuelve:

```
network=mainnet-demo syncMode=full
```

### 5. Verificar el chart antes de aplicar (equivalente a helm-diff)

```bash
helm template mini-eth ./chart -f demo-values.yaml | less
helm lint ./chart -f demo-values.yaml
```

### 6. Limpiar

```bash
helm uninstall mini-eth
kind delete cluster --name eth-demo
```

## Estructura

```
implementacion-helm-charts-ethereum/
├── README.md
├── demo-values.yaml           # override, análogo a ethereum-mainnet-values.yaml del post
└── chart/
    ├── Chart.yaml
    ├── values.yaml             # valores por defecto (imagen, red, resources, persistence)
    └── templates/
        ├── deployment.yaml     # Deployment + PVC
        └── service.yaml        # Service ClusterIP en el puerto RPC
```
