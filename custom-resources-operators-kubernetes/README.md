# Kubernetes CRDs y Custom Operators: mini-operador en bash

Post relacionado: [Kubernetes CRDs: Extendiendo la API nativa con recursos personalizados](https://www.devopsfreelance.pro/blog/posts/custom-resources-operators-kubernetes/)

## Qué demuestra este ejemplo

El post explica dos capas que suelen confundirse:

1. El **CRD** por sí solo ya aporta valor: define un nuevo tipo de recurso,
   con un esquema OpenAPI v3 que el API server valida antes de guardar nada
   en etcd, y un subrecurso `status` que separa estado deseado de estado real.
2. El **custom operator** es lo que le da vida a ese recurso: un controller
   que observa los objetos y ejecuta un ciclo de reconciliación
   (observar -> analizar -> ejecutar -> actualizar estado) para converger
   hacia el spec declarado.

Este ejemplo aterriza ambas capas con un CRD `WebApp`
(`webapp.example.com/v1`) y un operator mínimo escrito en **bash + kubectl +
jq** (sin Go ni Operator SDK, para que se pueda leer y correr en minutos):

- `crd/webapp-crd.yaml`: define el recurso `WebApp` con `spec.image`,
  `spec.replicas` (1-10), `spec.domain` (con pattern) y `spec.port`, más el
  subrecurso `status` (`phase`, `observedGeneration`, `lastReconcileTime`).
- `examples/webapp-valid.yaml`: un Custom Resource válido.
- `examples/webapp-invalid.yaml`: un Custom Resource que viola el schema
  (`replicas` fuera de rango, `domain` con formato inválido) para comprobar
  que el API server lo rechaza **solo por tener el CRD instalado**, sin
  operator corriendo.
- `operator/operator.sh`: el controller. Cada pocos segundos lista los
  `WebApp` del namespace, crea/actualiza un `Deployment` y un `Service` por
  cada uno (`kubectl apply` es idempotente), escribe `status.phase=Ready`
  vía `kubectl patch --subresource=status`, y borra los recursos huérfanos
  cuando se elimina un `WebApp`.

No implementa RBAC granular, finalizers, leader election ni multi-versión de
CRD (eso queda fuera de un mini-ejemplo); el foco está en dejar ver, con
logs en vivo, el ciclo de reconciliación y la diferencia entre "el CRD ya
valida" y "el operator ya actúa".

## Requisitos

- Docker (o Podman) corriendo localmente
- [kind](https://kind.sigs.k8s.io/) >= 0.20 (`kind version`)
- `kubectl` >= 1.26
- `jq`

Instalación rápida en Linux si falta algo:

```bash
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.23.0/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind
sudo apt-get install -y jq   # o el gestor de paquetes de tu distro
```

## Estructura

```
custom-resources-operators-kubernetes/
├── crd/
│   └── webapp-crd.yaml          # CustomResourceDefinition: WebApp (webapp.example.com/v1)
├── operator/
│   └── operator.sh              # Controller: reconciliation loop en bash + kubectl + jq
└── examples/
    ├── webapp-valid.yaml        # Custom Resource válido
    └── webapp-invalid.yaml      # Custom Resource que el schema del CRD rechaza
```

## Pasos para correrlo

Desde el directorio `custom-resources-operators-kubernetes/`:

```bash
# 1. Crear un cluster local con kind (tarda 1-2 minutos)
kind create cluster --name crd-demo

# 2. Instalar el CRD WebApp en el cluster
kubectl apply -f crd/webapp-crd.yaml
kubectl get crd webapps.webapp.example.com

# 3. Probar la validación del schema SIN ningún operator corriendo
kubectl apply -f examples/webapp-invalid.yaml
# -> el API server debe rechazarlo (error de validación, "Invalid value")

# 4. Dar permiso de ejecución y arrancar el operator (queda corriendo en foreground)
chmod +x operator/operator.sh
./operator/operator.sh
```

En otra terminal, con el operator corriendo:

```bash
# 5. Crear un Custom Resource válido -> dispara la reconciliación
kubectl apply -f examples/webapp-valid.yaml

# 6. Ver qué creó el operator a partir del Custom Resource
kubectl get webapps.webapp.example.com -o wide
kubectl get deployment demo-app
kubectl get service demo-app
kubectl get pods -l app=demo-app

# 7. Ver el status que el operator escribió en el Custom Resource
kubectl get webapp demo-app -o jsonpath='{.status}' | jq .

# 8. Modificar el spec (por ejemplo, escalar) y ver que el operator reconcilia de nuevo
kubectl patch webapp demo-app --type merge -p '{"spec":{"replicas":4}}'
kubectl get pods -l app=demo-app

# 9. Borrar el Custom Resource y ver que el operator limpia el Deployment/Service
kubectl delete -f examples/webapp-valid.yaml
kubectl get deployment demo-app   # -> Error from server (NotFound)

# 10. Limpiar todo
# Ctrl+C en la terminal del operator, luego:
kind delete cluster --name crd-demo
```

## Salida esperada

Al aplicar `examples/webapp-invalid.yaml` (paso 3), sin operator corriendo:

```
The WebApp "broken-app" is invalid:
* spec.replicas: Invalid value: 25: spec.replicas in body should be less than or equal to 10
* spec.domain: Invalid value: "dominio invalido": spec.domain in body should match '^[a-z0-9]...'
```

En la terminal del operator, al aplicar `examples/webapp-valid.yaml` (paso 5):

```
2026-01-15 10:00:00 [operator] Operator iniciado. Observando WebApp en namespace 'default' cada 5s...
2026-01-15 10:00:05 [operator] Reconciliando WebApp 'demo-app' (image=nginxdemos/hello:plain-text, replicas=2)
2026-01-15 10:00:05 [operator] WebApp 'demo-app' reconciliada -> status.phase=Ready
```

`kubectl get webapps.webapp.example.com -o wide`:

```
NAME       IMAGE                             REPLICAS   DOMAIN              PHASE   AGE
demo-app   nginxdemos/hello:plain-text       2          demo.example.com    Ready   10s
```

`kubectl get pods -l app=demo-app`:

```
NAME                        READY   STATUS    RESTARTS   AGE
demo-app-6d8f9c9c7f-abcde   1/1     Running   0          8s
demo-app-6d8f9c9c7f-fghij   1/1     Running   0          8s
```

Al hacer `kubectl patch ... replicas:4` (paso 8), en el siguiente ciclo (máx.
5s) el operator vuelve a loguear `Reconciliando WebApp 'demo-app' (... replicas=4)`
y aparecen 2 pods adicionales. Al borrar el Custom Resource (paso 9), en el
siguiente ciclo aparece:

```
2026-01-15 10:05:10 [operator] WebApp 'demo-app' ya no existe, eliminando deployment huérfano
2026-01-15 10:05:10 [operator] WebApp 'demo-app' ya no existe, eliminando service huérfano
```

## Notas

- No se usan credenciales ni cuentas cloud: todo corre en contenedores
  locales vía `kind`, y `operator.sh` usa el kubeconfig local
  (`~/.kube/config`) igual que `kubectl`.
- La imagen `nginxdemos/hello:plain-text` es pública y gratuita; solo
  responde con texto plano, se usa para tener un contenedor real y liviano
  como carga de trabajo gestionada.
- Este operator hace *polling* cada `RESYNC_SECONDS` en vez de usar `watch`,
  a propósito, para no depender de ninguna librería cliente de Kubernetes:
  con `kubectl` y `jq` alcanza para ver el patrón completo. En producción,
  este mismo ciclo se implementa con el Operator SDK/Kubebuilder en Go (como
  se menciona en el post), con `watch` real, RBAC restrictivo, finalizers y
  leader election.
