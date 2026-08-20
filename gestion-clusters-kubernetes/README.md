# Gestión Multi-Cluster de Kubernetes: ejemplo práctico con kind

Post relacionado: [Gestión Cluster Kubernetes: Guía Completa para DevOps 2025](https://www.devopsfreelance.pro/blog/posts/gestion-clusters-kubernetes/)

## Qué demuestra este ejemplo

El post describe arquitecturas (hub-and-spoke, peer-to-peer, híbrida) y herramientas
(Rancher Fleet, Karmada, ArgoCD, Prometheus federado) para administrar varios
clusters de Kubernetes a la vez. Reproducir esas herramientas completas no es
viable en una máquina local, así que este ejemplo aterriza el concepto central
del post -gestionar múltiples clusters desde un único punto de control- con
herramientas 100% locales y gratuitas:

- Levanta **dos clusters Kubernetes independientes** (`prod` y `staging`) con `kind`.
- Despliega el **mismo manifest** en ambos clusters desde un solo script,
  etiquetando cada namespace con su entorno (equivalente simplificado a lo que
  hacen Fleet/Karmada/ArgoCD ApplicationSets al propagar recursos entre clusters).
- Consulta el **estado agregado** (nodos, capacidad, pods) de todos los clusters
  desde un único script, simulando la vista centralizada que en producción
  daría un dashboard de Grafana con Prometheus federado.

No implementa service mesh multi-cluster, GitOps ni políticas OPA/Gatekeeper (esa
parte del post es más conceptual); se enfoca en el flujo mínimo real de
"un comando gestiona N clusters".

## Requisitos

- Docker (o Podman) corriendo localmente
- [kind](https://kind.sigs.k8s.io/) >= 0.20 (`kind version`)
- `kubectl` >= 1.26
- Bash

Instalación rápida de kind (Linux):

```bash
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.23.0/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind
```

## Estructura

```
gestion-clusters-kubernetes/
├── kind/
│   ├── cluster-prod.yaml       # config kind: cluster prod (control-plane + worker)
│   └── cluster-staging.yaml    # config kind: cluster staging (1 nodo)
├── manifests/
│   └── app-deployment.yaml     # Deployment + Service de la app demo
└── scripts/
    ├── create-clusters.sh      # crea los 2 clusters kind
    ├── deploy-all.sh           # despliega el manifest en ambos clusters
    ├── cluster-status.sh       # vista agregada de nodos/pods de ambos clusters
    └── cleanup.sh              # borra los 2 clusters
```

## Pasos para correrlo

Desde el directorio `gestion-clusters-kubernetes/`:

```bash
# 1. Crear los dos clusters (tarda 1-3 minutos, descarga la imagen de kind)
./scripts/create-clusters.sh

# 2. Desplegar la misma app en ambos clusters de forma centralizada
./scripts/deploy-all.sh

# 3. Ver el estado agregado de todos los clusters gestionados
./scripts/cluster-status.sh

# 4. (Opcional) Probar la app en cualquiera de los clusters
kubectl --context kind-prod -n demo port-forward svc/demo-app 8080:80
# abrir http://localhost:8080 en otra terminal

# 5. Limpiar todo al terminar
./scripts/cleanup.sh
```

## Salida esperada

Tras `create-clusters.sh`:

```
Clusters disponibles:
prod
staging

Contextos de kubectl generados:
kind-prod             kind-prod             kind-prod
kind-staging          kind-staging          kind-staging
```

Tras `deploy-all.sh`, para cada cluster:

```
=== Desplegando en cluster 'prod' (contexto: kind-prod) ===
namespace/demo created
namespace/demo labeled
deployment.apps/demo-app created
service/demo-app created
deployment "demo-app" successfully rolled out
```

Tras `cluster-status.sh`, por cada cluster verás algo como:

```
===================================================
 Cluster: prod  (contexto: kind-prod)
===================================================
-- Nodos y capacidad --
NAME                 CPU   MEMORY
prod-control-plane   8     16393216Ki
prod-worker          8     16393216Ki

-- Pods de la app demo (namespace demo) --
NAME                        READY   STATUS    ...
demo-app-6d8f9c9c7f-abcde   1/1     Running   ...
demo-app-6d8f9c9c7f-fghij   1/1     Running   ...
```

(los valores exactos de CPU/memoria dependen de tu máquina).

## Notas

- No se usan credenciales ni cuentas cloud: todo corre en contenedores locales vía kind.
- La imagen `nginxdemos/hello` es pública y gratuita, solo para tener algo que
  responder HTTP y verificar que el "multi-cluster" realmente sirve tráfico en
  ambos entornos.
- `kind get clusters` / `kubectl config get-contexts` sirven para inspeccionar
  en cualquier momento qué clusters y contextos quedaron registrados.
