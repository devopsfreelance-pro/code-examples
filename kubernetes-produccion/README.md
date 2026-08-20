# Kubernetes en producción: ejemplo práctico con kind

Post relacionado: [Guía Completa de Kubernetes en producción](https://www.devopsfreelance.pro/blog/posts/kubernetes-produccion/)

## Qué demuestra este ejemplo

El post cubre las prácticas que separan un cluster de laboratorio de uno
listo para producción: resource requests/limits, LimitRange, autoescalado
(HPA/VPA/Cluster Autoscaler), health checks (liveness/readiness/startup),
NetworkPolicy, RBAC, backup de etcd y PodDisruptionBudget. Reproducir todo
eso (control plane HA, etcd real, RBAC contra un IdP) no es viable en una
laptop, así que este ejemplo aterriza las prácticas que sí se pueden
verificar en minutos con un cluster local:

- Un **Deployment con requests/limits explícitos** y un **LimitRange** de
  namespace, igual que en el post.
- Las **tres probes** (liveness, readiness, startup) configuradas y
  verificables con `kubectl`.
- Un **HorizontalPodAutoscaler** funcional (con `metrics-server` instalado
  y parcheado para kind).
- Un **PodDisruptionBudget** que protege un mínimo de réplicas.
- Dos **NetworkPolicy** (deny-all-ingress + allow selectivo por label),
  igual patrón que el post.

No incluye HA de control plane, backup de etcd real ni RBAC (esas partes
dependen de infraestructura administrada por el proveedor cloud y no se
pueden probar de forma realista en un cluster local de un solo comando).

### Nota importante sobre NetworkPolicy en kind

El CNI por defecto de `kind` (kindnet) **no aplica** NetworkPolicy: los
manifiestos se crean correctamente en la API pero el tráfico no se bloquea
de verdad. El script `verificar.sh` igual las aplica y prueba el acceso
para que veas el patrón (deny-all + allow selectivo tal como lo recomienda
el post); si el paso 5 no bloquea el tráfico, es una limitación conocida
de kindnet, no un error del manifiesto. Para ver el bloqueo real, instalá
Calico en el cluster kind (`kind create cluster` + Calico CNI) o usá
`minikube start --cni=calico`.

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
kubernetes-produccion/
├── kind-cluster.yaml   # config kind: 1 control-plane + 2 workers
├── manifests.yaml      # Namespace, LimitRange, Deployment, Service, HPA, NetworkPolicy, PDB
├── deploy.sh           # crea el cluster, instala metrics-server, aplica los manifiestos
├── verificar.sh        # verifica requests/limits, probes, PDB, HPA y NetworkPolicy
└── cleanup.sh           # borra el cluster
```

## Pasos para correrlo

Desde el directorio `kubernetes-produccion/`:

```bash
chmod +x deploy.sh verificar.sh cleanup.sh

# 1. Crear el cluster y desplegar todo
./deploy.sh

# 2. Verificar las prácticas de producción (probes, PDB, HPA, NetworkPolicy)
./verificar.sh

# 3. (opcional) Generar carga y observar al HPA escalar réplicas
kubectl run -n production carga --rm -i --restart=Never --image=busybox:1.36 \
  --command -- /bin/sh -c "while true; do wget -q -O- http://api-demo.production.svc.cluster.local; done" &
watch kubectl get hpa api-demo-hpa -n production
# Cortar con Ctrl+C y luego: kubectl delete pod carga -n production --ignore-not-found

# 4. Borrar todo
./cleanup.sh
```

## Salida esperada

Al final de `deploy.sh`:

```
Listo. Estado actual:
NAME                        READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/api-demo    3/3     3            3           45s

NAME                             READY   STATUS    RESTARTS   AGE
pod/api-demo-xxxxxxxxxx-xxxxx    1/1     Running   0          40s
pod/api-demo-xxxxxxxxxx-yyyyy    1/1     Running   0          40s
pod/api-demo-xxxxxxxxxx-zzzzz    1/1     Running   0          40s

NAME                                            REFERENCE               TARGETS  MINPODS  MAXPODS  REPLICAS
horizontalpodautoscaler.autoscaling/api-demo-hpa Deployment/api-demo    0%/50%   3        8        3

NAME                                     MIN AVAILABLE   ALLOWED DISRUPTIONS   AGE
poddisruptionbudget.policy/api-demo-pdb  2               1                    45s

NAME                                                  POD-SELECTOR   AGE
networkpolicy.networking.k8s.io/allow-client-to-api   app=api-demo   45s
networkpolicy.networking.k8s.io/deny-all-ingress      <none>         45s
```

`verificar.sh` imprime los requests/limits por pod, las rutas de cada
probe, el estado del PDB y del HPA, y termina probando el acceso a la
Service con y sin el label `role=client` (ver nota sobre kindnet arriba).

Bajo carga sostenida (paso 3), el HPA debería escalar de 3 a más réplicas
cuando el uso de CPU supere el 50% definido en `manifests.yaml`.

## Limpieza

```bash
./cleanup.sh
```

Borra el cluster kind completo; no queda nada corriendo en la máquina.
