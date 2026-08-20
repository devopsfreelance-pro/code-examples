# Pod Security Standards en accion: rechazar vs. admitir pods

Ejemplo de codigo que acompana al post [Guía Completa de Kubernetes security best practices](https://www.devopsfreelance.pro/blog/posts/kubernetes-security-best-practices/).

## Que demuestra

El post cubre varias capas de seguridad en Kubernetes (Pod Security Standards, RBAC, Network Policies, gestion de secrets, escaneo de imagenes, Falco, SecurityContext, CIS Benchmark). Este ejemplo se enfoca en la primera linea de defensa, que es la que se puede reproducir de punta a punta en minutos sin dependencias externas: **Pod Security Admission**.

Se crea un namespace `secure-demo` etiquetado con el nivel `restricted`, y luego:

1. Se intenta crear un pod **inseguro** (privilegiado, corre como root, con todas las capabilities de Linux) → el API server lo **rechaza** automaticamente, sin que haga falta ningun admission controller externo.
2. Se crea un pod **seguro**, endurecido segun la seccion "SecurityContext en pods" del post (`runAsNonRoot`, `readOnlyRootFilesystem`, `capabilities: drop: [ALL]`, `seccompProfile: RuntimeDefault`) → el API server lo **admite** y el pod llega a `Ready`.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/) (o Podman) corriendo localmente.
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) (Kubernetes in Docker) v0.20 o superior.
- [kubectl](https://kubernetes.io/docs/tasks/tools/) v1.27 o superior (Pod Security Admission es GA desde v1.25).

No se necesita ninguna cuenta ni servicio pago: todo corre en un cluster kind local.

## Archivos

- `namespace.yaml` — Namespace `secure-demo` con las tres etiquetas de Pod Security Admission en modo `restricted`.
- `insecure-pod.yaml` — Pod privilegiado que debe ser rechazado por el API server.
- `secure-pod.yaml` — Pod endurecido (non-root, filesystem read-only, sin capabilities, seccomp) que debe ser admitido.
- `demo.sh` — Script que orquesta todo el flujo: crea el cluster kind, aplica el namespace, intenta ambos pods y muestra el resultado.

## Pasos para correrlo

```bash
cd kubernetes-security-best-practices

# Dar permisos de ejecucion al script (una sola vez)
chmod +x demo.sh

# Correr la demo completa
./demo.sh
```

El script es idempotente: si el cluster `pss-demo` ya existe lo reutiliza.

### Limpieza

```bash
kind delete cluster --name pss-demo
```

## Salida esperada

Al final de `./demo.sh` deberias ver algo como:

```
== Intentando crear el pod INSEGURO (se espera que sea RECHAZADO) ==
Error from server (Forbidden): error when creating "insecure-pod.yaml": pods "insecure-pod" is forbidden: violates PodSecurity "restricted:latest": ...
OK: el API server rechazo el pod inseguro por violar el nivel 'restricted'.

== Creando el pod SEGURO (se espera que sea ADMITIDO) ==
pod/secure-pod created

== Esperando a que 'secure-pod' este Ready (timeout 60s) ==
pod/secure-pod condition met

== Estado final de los pods en el namespace secure-demo ==
NAME          READY   STATUS    RESTARTS   AGE   IP           NODE
secure-pod    1/1     Running   0          5s    10.244.x.x   pss-demo-control-plane
```

Notar que `insecure-pod` **no aparece** en el listado final: nunca llego a crearse porque el API server lo rechazo en la etapa de admision, antes de que el scheduler lo tocara.

## Ir mas alla

Para verificar manualmente por que se rechaza el pod inseguro:

```bash
kubectl apply -f insecure-pod.yaml
```

Para inspeccionar el detalle del pod seguro ya corriendo:

```bash
kubectl describe pod secure-pod -n secure-demo
```

Este ejemplo no cubre RBAC, Network Policies, gestion de secrets, escaneo de imagenes con Trivy/Kyverno ni runtime security con Falco (temas tambien tratados en el post): son practicas complementarias que requieren mas piezas moviles (CNI con soporte de NetworkPolicy, un registry, un admission controller externo) y quedan fuera del alcance de este mini-ejemplo.
