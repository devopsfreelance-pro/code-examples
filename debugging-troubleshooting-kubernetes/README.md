# Debugging y troubleshooting en Kubernetes: ejemplo práctico

Post relacionado: [Guía Completa de Debugging y troubleshooting kubernetes](https://www.devopsfreelance.pro/blog/posts/debugging-troubleshooting-kubernetes/)

## Qué demuestra este ejemplo

Este mini-laboratorio levanta un clúster local con [kind](https://kind.sigs.k8s.io/) y despliega
dos aplicaciones **rotas a propósito** para practicar las técnicas de diagnóstico explicadas en el post:

- **`crashy-app`**: un contenedor que falla al iniciar y entra en `CrashLoopBackOff`.
  Se diagnostica con `kubectl describe pod` (eventos) y `kubectl logs --previous`.
- **`notready-app`**: un contenedor que corre pero cuya `readinessProbe` apunta a un
  puerto/ruta que nunca responde, por lo que el pod queda `NotReady` indefinidamente.
- **`notready-app-svc`**: un `Service` cuyo `selector` no coincide con ningún pod,
  por lo que queda **sin endpoints** (`kubectl get endpoints` vacío).

El script `debug.sh` automatiza todo el recorrido: crea el clúster, aplica los manifiestos,
espera a que los pods fallen, y ejecuta los comandos de diagnóstico del post
(`describe`, `logs --previous`, `get endpoints`) mostrando su salida.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/) corriendo
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
- [kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl)

No se necesita cuenta ni credenciales de ningún cloud: todo corre en local, sobre Docker.

## Pasos para correrlo

```bash
cd debugging-troubleshooting-kubernetes

chmod +x debug.sh
./debug.sh
```

El script es idempotente: si el clúster `debug-demo` ya existe, lo reutiliza.

### Explorar manualmente (opcional)

Con el clúster ya levantado (`kubectl config use-context kind-debug-demo`):

```bash
# Ver estado general
kubectl get pods -n debug-demo -o wide

# Inspeccionar el pod que crashea
kubectl describe pod -n debug-demo -l app=crashy-app
kubectl logs -n debug-demo -l app=crashy-app --previous

# Inyectar un ephemeral container con herramientas de red/debug
kubectl debug -n debug-demo \
  "$(kubectl get pod -n debug-demo -l app=crashy-app -o jsonpath='{.items[0].metadata.name}')" \
  -it --image=busybox --target=crashy-app

# Ver por qué el Service no tiene endpoints
kubectl get endpoints notready-app-svc -n debug-demo
kubectl get service notready-app-svc -n debug-demo -o yaml
```

## Salida esperada

Al correr `./debug.sh` vas a ver algo similar a:

```
=== 4. kubectl get pods -o wide ===
NAME                            READY   STATUS             RESTARTS   AGE   IP           NODE
crashy-app-7f8d9c5f6b-abcde     0/1     CrashLoopBackOff   2          15s   10.244.0.5   debug-demo-control-plane
notready-app-6c9b8d4f5c-xyz12   0/1     Running            0          15s   10.244.0.6   debug-demo-control-plane

=== 5. Diagnóstico de crashy-app: describe + logs --previous ===
...
Events:
  ...  Warning  BackOff  ...  Back-off restarting failed container
...
--- kubectl logs ... --previous ---
iniciando app...
ERROR: no se encontro CONFIG_PATH

=== 7. Service sin endpoints (selector mal configurado) ===
NAME                ENDPOINTS   AGE
notready-app-svc     <none>     15s
```

Esto reproduce en miniatura los tres síntomas más comunes del post: `CrashLoopBackOff`,
pod `NotReady` por probe mal configurada, y `Service` sin endpoints por selector incorrecto.

## Limpieza

```bash
kind delete cluster --name debug-demo
```

## Archivos

- `kind-cluster.yaml`: definición del clúster local de un solo nodo.
- `manifests/broken-app.yaml`: namespace, dos deployments rotos y un service sin endpoints.
- `debug.sh`: automatiza creación del clúster, despliegue y comandos de diagnóstico.
