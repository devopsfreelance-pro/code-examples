# NetworkPolicies en accion: segmentacion por zonas (frontend/backend/database)

Ejemplo de codigo que acompana al post [Kubernetes Networking: Guía Completa para Arquitecturas Avanzadas](https://www.devopsfreelance.pro/blog/posts/kubernetes-networking-avanzado/).

## Que demuestra

El post cubre varias capas de kubernetes networking (CNI, Calico, network policies, service mesh). Este ejemplo se enfoca en la parte que se puede reproducir de punta a punta en minutos con herramientas locales y gratuitas: **network policies con enforcement real**, aplicando el mismo patron que describe el post en el caso de uso de comercio electronico (aislar la capa de datos del resto de la infraestructura, estilo PCI-DSS).

Se crean tres namespaces (`frontend`, `backend`, `database`), cada uno con un pod servidor, y se aplican NetworkPolicies siguiendo la estrategia de **denegacion por defecto + whitelist explicita** que recomienda el post:

1. **Antes** de aplicar policies: cualquier pod puede llamar a cualquier otro (comportamiento por defecto de Kubernetes).
2. **Despues** de aplicar policies:
   - `frontend` puede llamar a `backend` (permitido explicitamente).
   - `backend` puede llamar a `database` (permitido explicitamente).
   - `frontend` **ya no puede** llamar directo a `database` (bloqueado por `default-deny-ingress` + whitelist que solo acepta trafico desde `backend`).

Como kind no aplica NetworkPolicies con su CNI por defecto (kindnet), el script instala **Calico** en el cluster para tener enforcement real, tal como describe la seccion "Calico: Networking y Seguridad Empresarial" del post.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/) (o Podman) corriendo localmente.
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) v0.20 o superior.
- [kubectl](https://kubernetes.io/docs/tasks/tools/) v1.27 o superior.
- Conexion a internet para descargar el manifiesto de Calico (`raw.githubusercontent.com`) y la imagen `nginx:alpine`.

No se necesita ninguna cuenta ni servicio pago: todo corre en un cluster kind local.

## Archivos

- `kind-config.yaml` — Config de kind que desactiva el CNI por defecto (`disableDefaultCNI: true`) para poder instalar Calico despues.
- `01-namespaces.yaml` — Namespaces `frontend`, `backend` y `database`, cada uno con una label `zone` usada por las NetworkPolicies.
- `02-workloads.yaml` — Un Deployment + Service (`nginx:alpine`) por namespace, para tener algo que responda y algo con lo que probar conexiones salientes (`wget` viene incluido en la imagen).
- `03-network-policies.yaml` — Las policies: `default-deny-ingress` en `backend` y `database`, mas `allow-from-frontend` / `allow-from-backend` para habilitar solo el trafico necesario.
- `demo.sh` — Orquesta todo el flujo: crea el cluster, instala Calico, aplica namespaces y workloads, prueba conectividad sin policies, aplica las policies, y vuelve a probar conectividad mostrando el bloqueo.

## Pasos para correrlo

```bash
cd kubernetes-networking-avanzado

# Dar permisos de ejecucion al script (una sola vez)
chmod +x demo.sh

# Correr la demo completa (tarda 2-4 minutos, sobre todo por Calico)
./demo.sh
```

El script es idempotente: si el cluster `netpol-demo` ya existe lo reutiliza.

### Limpieza

```bash
kind delete cluster --name netpol-demo
```

## Salida esperada

Al final de `./demo.sh` deberias ver algo como:

```
== PASO 1: probando conectividad ANTES de aplicar NetworkPolicies (deberia funcionar todo) ==
-- frontend -> database (sin policies, deberia responder) --
OK: frontend llega a database (esperado, todavia no hay policies)

== PASO 2: aplicando NetworkPolicies (deny-all + whitelist por zona) ==
networkpolicy.networking.k8s.io/default-deny-ingress created
networkpolicy.networking.k8s.io/allow-from-frontend created
networkpolicy.networking.k8s.io/default-deny-ingress created
networkpolicy.networking.k8s.io/allow-from-backend created

== PASO 3: re-probando conectividad DESPUES de aplicar NetworkPolicies ==
-- frontend -> backend (debe seguir permitido) --
OK: frontend -> backend permitido, como se espera.

-- backend -> database (debe seguir permitido) --
OK: backend -> database permitido, como se espera.

-- frontend -> database (debe quedar BLOQUEADO por la policy) --
OK: frontend -> database bloqueado, tal como define la NetworkPolicy 'default-deny-ingress' + whitelist en database.

Demo completa. Para limpiar todo:
  kind delete cluster --name netpol-demo
```

El punto clave es el ultimo bloque: la misma llamada que funcionaba en el PASO 1 queda bloqueada en el PASO 3, sin haber tocado el codigo de ninguna aplicacion, solo aplicando manifiestos declarativos.

## Ir mas alla

Para inspeccionar una policy aplicada:

```bash
kubectl describe networkpolicy allow-from-backend -n database
```

Para ver el detalle de un bloqueo en tiempo real (deja la terminal corriendo y en otra proba `frontend -> database`):

```bash
kubectl exec -n frontend deploy/frontend -- wget -qO- --timeout=3 http://database.database.svc.cluster.local
```

Este ejemplo no cubre CNI custom (BGP con Calico entre nodos reales, eBPF con Cilium), GlobalNetworkPolicy, ni service mesh (Istio/Linkerd con mTLS, circuit breaking, canary deployments), temas tambien tratados en el post: requieren un cluster multi-nodo o piezas adicionales (control plane del mesh, sidecars) y quedan fuera del alcance de este mini-ejemplo, que se concentra en el mecanismo nativo de Kubernetes (NetworkPolicy) que sostiene todo lo demas.
