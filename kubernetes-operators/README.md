# Kubernetes Operators: mini-operador en Python con CRD

Post relacionado: [Kubernetes Operators: Guía Completa para Automatización 2025](https://www.devopsfreelance.pro/blog/posts/kubernetes-operators/)

## Qué demuestra este ejemplo

El post explica el patrón operator: un CRD que define un recurso personalizado
(`Database`) y un controller que ejecuta un **ciclo de reconciliación** (observar,
analizar, ejecutar, actualizar estado, requeue) para mantener el estado real de un
clúster alineado con el estado deseado declarado por el usuario.

Este ejemplo aterriza ese patrón con un operador real y mínimo, sin usar Go ni el
Operator SDK, para que se pueda ejecutar en minutos:

- Un **CRD** (`crd/database-crd.yaml`) que define el recurso `Database`
  (`example.com/v1alpha1`), con `spec.image`, `spec.replicas`, `spec.port` y un
  subresource `status`.
- Un **operator en Python** (`operator/operator.py`) que usa el cliente oficial de
  Kubernetes para:
  - Observar (`watch`) los recursos `Database` del namespace `default`.
  - Reconciliar: crear/actualizar un `Deployment` y un `Service` que representan la
    "base de datos" (en este ejemplo, un contenedor `postgres` real).
  - Actualizar `status.phase` del Custom Resource, igual que hace `Reconcile()` en
    el ejemplo en Go del post.
  - Limpiar los recursos hijos cuando se borra el `Database`.
- Un **Custom Resource de ejemplo** (`examples/sample-database.yaml`) para disparar
  la reconciliación.

No implementa RBAC granular, finalizers, leader election ni Operator Lifecycle
Manager (esa parte queda fuera del alcance de un mini-ejemplo); se enfoca en dejar
ver, con logs en vivo, el ciclo observar -> analizar -> ejecutar -> actualizar
estado que es el corazón del patrón operator.

## Requisitos

- Docker (o Podman) corriendo localmente
- [kind](https://kind.sigs.k8s.io/) >= 0.20 (`kind version`)
- `kubectl` >= 1.26
- Python 3.9+ y `pip`

Instalación rápida de kind (Linux):

```bash
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.23.0/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind
```

## Estructura

```
kubernetes-operators/
├── crd/
│   └── database-crd.yaml       # CustomResourceDefinition: Database (example.com/v1alpha1)
├── operator/
│   ├── operator.py             # Controller: watch + reconciliation loop
│   └── requirements.txt        # dependencia: kubernetes (cliente oficial)
└── examples/
    └── sample-database.yaml    # Custom Resource de ejemplo para probar el operator
```

## Pasos para correrlo

Desde el directorio `kubernetes-operators/`:

```bash
# 1. Crear un cluster local con kind (tarda 1-2 minutos)
kind create cluster --name operators-demo

# 2. Instalar el CRD Database en el cluster
kubectl apply -f crd/database-crd.yaml
kubectl get crd databases.example.com

# 3. Instalar dependencias del operator y arrancarlo (queda corriendo en foreground)
python3 -m venv .venv
source .venv/bin/activate
pip install -r operator/requirements.txt
python3 operator/operator.py
```

En otra terminal, con el operator corriendo:

```bash
# 4. Crear un Custom Resource Database -> dispara la reconciliación
kubectl apply -f examples/sample-database.yaml

# 5. Ver qué creó el operator a partir del Custom Resource
kubectl get database demo-db -o wide
kubectl get deployment demo-db
kubectl get service demo-db
kubectl get pods -l app=demo-db

# 6. Ver el status que el operator escribió en el Custom Resource
kubectl get database demo-db -o jsonpath='{.status}' | python3 -m json.tool

# 7. Modificar el recurso (por ejemplo, escalar) y ver que el operator reconcilia de nuevo
kubectl patch database demo-db --type merge -p '{"spec":{"replicas":3}}'
kubectl get pods -l app=demo-db

# 8. Borrar el Custom Resource y ver que el operator limpia el Deployment/Service
kubectl delete -f examples/sample-database.yaml
kubectl get deployment demo-db   # -> not found

# 9. Limpiar todo
# Ctrl+C en la terminal del operator, luego:
kind delete cluster --name operators-demo
```

## Salida esperada

En la terminal del operator, al aplicar `examples/sample-database.yaml`:

```
2026-01-15 10:00:01 [operator] INFO Operator iniciado. Observando Database en namespace 'default'...
2026-01-15 10:00:15 [operator] INFO Reconciliando Database 'demo-db' (image=postgres:16-alpine, replicas=2)
2026-01-15 10:00:15 [operator] INFO Deployment 'demo-db' creado
2026-01-15 10:00:15 [operator] INFO Service 'demo-db' creado
2026-01-15 10:00:15 [operator] INFO Database 'demo-db' reconciliada -> status.phase=Ready
```

`kubectl get database demo-db -o wide`:

```
NAME      IMAGE               REPLICAS   PHASE   AGE
demo-db   postgres:16-alpine  2          Ready   30s
```

`kubectl get pods -l app=demo-db`:

```
NAME                       READY   STATUS    RESTARTS   AGE
demo-db-6d8f9c9c7f-abcde   1/1     Running   0          25s
demo-db-6d8f9c9c7f-fghij   1/1     Running   0          25s
```

Al hacer `kubectl patch ... replicas:3`, en la terminal del operator aparece un
nuevo ciclo `MODIFIED` -> `Reconciliando Database 'demo-db' (... replicas=3)` y un
tercer pod se levanta. Al borrar el Custom Resource, aparece:

```
2026-01-15 10:05:40 [operator] INFO Database 'demo-db' eliminada, limpiando recursos hijos
2026-01-15 10:05:40 [operator] INFO Deployment 'demo-db' eliminado
2026-01-15 10:05:40 [operator] INFO Service 'demo-db' eliminado
```

## Notas

- No se usan credenciales ni cuentas cloud: todo corre en contenedores locales vía
  `kind`, y `operator.py` toma el kubeconfig local (`~/.kube/config`) igual que
  `kubectl`.
- La imagen `postgres:16-alpine` es pública y gratuita; se usa solo para tener un
  contenedor real que representa la "base de datos" gestionada, no para persistir
  datos (no hay volumen configurado).
- En producción, este mismo patrón se implementa con el Operator SDK/Kubebuilder en
  Go (como en el ejemplo de código del post), con RBAC restrictivo, finalizers para
  garantizar la limpieza y leader election para correr en alta disponibilidad.
