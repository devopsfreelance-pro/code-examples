# GitOps con Kubernetes: mini reconciler local

Post: [Guía Completa de GitOps con Kubernetes](https://www.devopsfreelance.pro/blog/posts/gitops-con-kubernetes/)

## Qué demuestra

El post explica el principio central de GitOps: Git es la fuente única de
verdad, y un operador (Flux, ArgoCD, etc.) monitorea continuamente el
cluster, compara su estado real contra lo declarado en Git y corrige
cualquier divergencia sin intervención manual.

Este ejemplo reproduce ese loop de reconciliación con un script bash
(`gitops-reconciler.sh`) sobre un cluster `kind` local, sin instalar Flux
ni ArgoCD (que requieren más recursos y configuración). El script:

1. Toma un directorio de manifests de Kubernetes (`manifests/`) como si
   fuera el checkout de un repo Git.
2. Cada N segundos ejecuta `kubectl diff -k manifests/` para detectar
   divergencias entre el cluster y lo declarado.
3. Si hay drift, ejecuta `kubectl apply -k manifests/` para reconciliar,
   igual que haría un operador GitOps real al ver un commit nuevo o un
   cambio manual no autorizado en el cluster.

Vas a ver esto en acción provocando drift manual con `kubectl scale` y
observando cómo el reconciler lo revierte automáticamente al estado
declarado en `manifests/deployment.yaml` (2 réplicas).

## Requisitos

- Docker (o Podman) corriendo localmente.
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) instalado.
- `kubectl` instalado.

No se necesita cuenta de nube ni credenciales: todo corre en un cluster
Kubernetes local dentro de un contenedor.

## Pasos

### 1. Crear el cluster local

```bash
kind create cluster --config kind-cluster.yaml
kubectl cluster-info --context kind-gitops-demo
```

### 2. Dar permisos de ejecución al reconciler

```bash
chmod +x gitops-reconciler.sh
```

### 3. Arrancar el "operador GitOps" en una terminal

```bash
./gitops-reconciler.sh manifests demo-app 5
```

Salida esperada (primer ciclo, aplica el estado inicial):

```
GitOps reconciler iniciado.
Fuente de verdad (Git): manifests
Namespace destino: demo-app
Intervalo de sincronizacion: 5s
Presiona Ctrl+C para detener.

[10:00:00] Drift detectado respecto al estado declarado en Git. Reconciliando...
namespace/demo-app unchanged
deployment.apps/demo-webapp created
service/demo-webapp created
[10:00:05] Estado del cluster == estado en Git. Sin cambios.
[10:00:10] Estado del cluster == estado en Git. Sin cambios.
```

### 4. En otra terminal, verificar que el deployment está arriba

```bash
kubectl get deployment demo-webapp -n demo-app
kubectl get pods -n demo-app
```

Deberías ver 2 réplicas `Running`, tal como lo declara
`manifests/deployment.yaml`.

### 5. Simular un cambio manual no autorizado (drift)

Esto simula a alguien haciendo `kubectl scale` directo en producción, sin
pasar por Git, algo que GitOps está diseñado para detectar y revertir:

```bash
kubectl scale deployment demo-webapp -n demo-app --replicas=5
kubectl get pods -n demo-app
```

Vas a ver momentáneamente 5 pods.

### 6. Observar la reconciliación automática

Volvé a la terminal donde corre `gitops-reconciler.sh`. Dentro del
intervalo configurado (5s) vas a ver algo como:

```
[10:01:15] Drift detectado respecto al estado declarado en Git. Reconciliando...
deployment.apps/demo-webapp configured
[10:01:20] Estado del cluster == estado en Git. Sin cambios.
```

Y al volver a listar los pods:

```bash
kubectl get pods -n demo-app
```

Vuelven a ser 2, el número declarado en `manifests/deployment.yaml`. Esto
es exactamente el "self-heal" que hacen Flux (`Kustomization.spec.prune`)
y ArgoCD (`syncPolicy.automated.selfHeal`) descritos en el post, aplicado
de forma simplificada.

### 7. Limpiar

```bash
# Ctrl+C en la terminal del reconciler
kind delete cluster --name gitops-demo
```

## Notas

- `nginxdemos/hello:plain-text` es una imagen pública liviana sin
  dependencias externas ni credenciales.
- El script no reemplaza herramientas GitOps de producción (no tiene
  webhooks, autenticación a repos Git, RBAC granular, ni pruning
  automático de recursos eliminados). Es una simplificación pedagógica
  del concepto central del post.
