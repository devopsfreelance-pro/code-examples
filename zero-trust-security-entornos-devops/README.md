# Zero Trust Security en entornos DevOps: microsegmentación con NetworkPolicy en Kubernetes

Post relacionado: [Guía definitiva de Zero Trust Security en entornos DevOps](https://www.devopsfreelance.pro/blog/posts/zero-trust-security-entornos-devops/)

## Qué demuestra este ejemplo

El post menciona la microsegmentación como uno de los componentes clave de
Zero Trust ("nunca confiar, siempre verificar") y cita a Calico como
herramienta típica para implementarla en Kubernetes. Este ejemplo levanta
un clúster local con Calico y aplica ese principio de forma muy concreta:

1. Se despliegan tres workloads que simulan una app de tres capas:
   `frontend`, `backend` y `database`.
2. Se aplica una `NetworkPolicy` de **default-deny** en el namespace: por
   defecto ningún pod puede hablar con otro (esto es "nunca confiar").
3. Se agregan políticas de **allow explícito y mínimo privilegio**:
   - `frontend` puede llamar a `backend` (y nada más).
   - `backend` puede llamar a `database` (y nada más).
   - `frontend` **no puede** llegar directo a `database`: sin regla de
     allow, el tráfico queda bloqueado (esto es "siempre verificar" +
     "menor privilegio", los mismos principios que el post describe).
4. Un script (`test-zero-trust.sh`) valida con `curl` desde dentro del
   clúster que las conexiones permitidas funcionan y que la conexión no
   autorizada (frontend -> database) es efectivamente rechazada, tal como
   describe el caso de uso del banco del post ("eliminación de accesos no
   autorizados a producción").

Todo el enforcement de las `NetworkPolicy` lo hace Calico, que es la misma
herramienta que el post nombra explícitamente para microsegmentación en
Kubernetes.

## Requisitos

- Docker (o Podman) corriendo localmente.
- [kind](https://kind.sigs.k8s.io/) (Kubernetes in Docker).
- `kubectl`.
- Conexión a internet para bajar la imagen del clúster y el manifest de
  Calico (no se usa ningún servicio pago ni cuenta cloud).

## Cómo correrlo

### 1. Crear el clúster (sin el CNI por defecto)

```bash
kind create cluster --config kind-config.yaml
```

### 2. Instalar Calico (motor que aplica las NetworkPolicy)

```bash
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/calico.yaml

# Esperar a que todos los pods de Calico y CoreDNS estén Ready
kubectl -n kube-system rollout status deployment/calico-kube-controllers --timeout=180s
kubectl -n kube-system rollout status deployment/coredns --timeout=180s
```

### 3. Desplegar la app de ejemplo (namespace + 3 workloads)

```bash
kubectl apply -f manifests/00-namespace.yaml
kubectl apply -f manifests/01-workloads.yaml

kubectl -n zero-trust-demo rollout status deployment/frontend --timeout=120s
kubectl -n zero-trust-demo rollout status deployment/backend --timeout=120s
kubectl -n zero-trust-demo rollout status deployment/database --timeout=120s
```

### 4. Probar el acceso ANTES de aplicar Zero Trust (todo abierto)

```bash
FRONTEND_POD=$(kubectl -n zero-trust-demo get pod -l app=frontend -o jsonpath='{.items[0].metadata.name}')
kubectl -n zero-trust-demo exec "$FRONTEND_POD" -- curl -s -o /dev/null -w "frontend -> database: %{http_code}\n" http://database.zero-trust-demo.svc.cluster.local
```

Esto debería devolver `200`: sin Zero Trust, cualquier pod habla con
cualquier otro. Este es exactamente el modelo de confianza implícita que
el post dice que hay que eliminar.

### 5. Aplicar las políticas Zero Trust

```bash
kubectl apply -f manifests/02-default-deny.yaml
kubectl apply -f manifests/03-allow-dns.yaml
kubectl apply -f manifests/04-allow-frontend-to-backend.yaml
kubectl apply -f manifests/05-allow-backend-to-database.yaml
```

### 6. Verificar el comportamiento Zero Trust

```bash
chmod +x test-zero-trust.sh
./test-zero-trust.sh
```

### Salida esperada

```
==> frontend -> backend (permitido)
    OK: resultado=allow (esperado=allow)
==> backend -> database (permitido)
    OK: resultado=allow (esperado=allow)
==> frontend -> database (debe estar bloqueado)
    OK: resultado=deny (esperado=deny)

Todas las verificaciones de Zero Trust pasaron.
```

### 7. Limpiar

```bash
kind delete cluster --name zero-trust-demo
```

## Notas

- El clúster deshabilita el CNI por defecto de `kind` (`kindnet`) porque
  no aplica `NetworkPolicy`. Calico sí lo hace, igual que en un clúster
  EKS/GKE/AKS real usando Calico como motor de políticas.
- Este ejemplo cubre un solo pilar de Zero Trust (microsegmentación de
  red). El post también menciona IAM, MFA, cifrado y SIEM, que quedan
  fuera del alcance de este mini ejemplo para mantenerlo simple y
  ejecutable en minutos.
