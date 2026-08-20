# Docker Swarm vs Kubernetes: el mismo servicio en ambas plataformas

Ejemplo de código del post [Docker Swarm vs Kubernetes: Guía completa para elegir 2026](https://www.devopsfreelance.pro/blog/posts/docker-swarm-vs-kubernetes/).

## Qué demuestra

El post compara Docker Swarm y Kubernetes en teoría. Acá se despliega **el mismo
servicio** (`traefik/whoami`, una imagen mínima que devuelve el hostname del
contenedor que atendió la petición) en las dos plataformas, para ver en la
práctica los conceptos centrales del artículo:

- **Réplicas y balanceo de carga**: 3 réplicas del servicio, y cada petición
  puede ser atendida por un contenedor distinto (se ve en el campo
  `Hostname` de la respuesta).
- **Rolling update**: en Swarm vía `update_config` del stack; en Kubernetes
  vía `strategy.rollingUpdate` del Deployment.
- **Complejidad relativa**: Swarm necesita un único archivo y dos comandos.
  Kubernetes necesita un Deployment, un Service y (para levantar el cluster
  local) un cluster kind aparte, tal como describe el post sobre curva de
  aprendizaje y arquitectura.

## Requisitos

- Docker Engine 20.10+ (con soporte para Swarm mode, viene incluido).
- Para la parte de Kubernetes: [kind](https://kind.sigs.k8s.io/) y `kubectl`.
  No hace falta ninguna cuenta ni servicio pago: todo corre localmente.

## Parte 1: Docker Swarm

```bash
# Inicializar el modo Swarm (un único nodo local alcanza para la demo)
docker swarm init

# Desplegar el stack (equivalente a "aplicar el manifiesto")
docker stack deploy -c docker-compose.stack.yml demo

# Ver el estado del servicio y sus réplicas
docker stack services demo
docker service ps demo_web

# Probar el balanceo de carga: cada curl puede volver con un Hostname distinto
for i in 1 2 3 4 5; do curl -s http://localhost:8000 | grep Hostname; done

# Escalar en caliente
docker service scale demo_web=5
docker service ps demo_web

# Actualizar la imagen (rolling update con rollback automático si falla)
docker service update --image traefik/whoami:v1.10 demo_web

# Limpiar
docker stack rm demo
docker swarm leave --force
```

### Salida esperada

```
$ docker stack services demo
ID             NAME       MODE        REPLICAS   IMAGE                   PORTS
xxxxxxxxxxxx   demo_web   replicated  3/3        traefik/whoami:v1.10   *:8000->80/tcp

$ curl -s http://localhost:8000 | grep Hostname
Hostname: a1b2c3d4e5f6
$ curl -s http://localhost:8000 | grep Hostname
Hostname: f6e5d4c3b2a1
```

## Parte 2: Kubernetes (con kind)

```bash
# Crear un cluster local de un solo nodo con el puerto 8080 mapeado al NodePort
kind create cluster --name swarm-vs-k8s --config k8s/kind-config.yaml

# Aplicar namespace, Deployment y Service
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml

# Ver el estado de los pods (equivalente a "docker service ps")
kubectl get pods -n demo
kubectl get deployment,svc -n demo

# Probar el balanceo de carga: el Service reparte entre los 3 pods
for i in 1 2 3 4 5; do curl -s http://localhost:8080 | grep Hostname; done

# Escalar en caliente
kubectl scale deployment/whoami -n demo --replicas=5
kubectl get pods -n demo

# Rolling update (forzamos un redeploy para verlo en acción)
kubectl rollout restart deployment/whoami -n demo
kubectl rollout status deployment/whoami -n demo

# Limpiar
kind delete cluster --name swarm-vs-k8s
```

### Salida esperada

```
$ kubectl get pods -n demo
NAME                     READY   STATUS    RESTARTS   AGE
whoami-6d8f9c7b5d-2xk9p  1/1     Running   0          10s
whoami-6d8f9c7b5d-7mjqz  1/1     Running   0          10s
whoami-6d8f9c7b5d-p4t8w  1/1     Running   0          10s

$ curl -s http://localhost:8080 | grep Hostname
Hostname: whoami-6d8f9c7b5d-2xk9p
```

## Comparación directa

| Aspecto | Docker Swarm | Kubernetes |
|---|---|---|
| Archivos necesarios | 1 (`docker-compose.stack.yml`) | 3 (namespace, deployment, kind-config) |
| Comandos para desplegar | 2 (`swarm init`, `stack deploy`) | 3+ (`kind create`, `kubectl apply` x2) |
| Balanceo de carga | Routing mesh integrado | Service (kube-proxy) |
| Escalado | `docker service scale` | `kubectl scale` |
| Rollback automático | `failure_action: rollback` en el stack | `kubectl rollout undo` (manual) |

Esta tabla resume en código lo que el post explica en prosa: Swarm resuelve lo
mismo con menos piezas, Kubernetes expone más controles (probes, estrategia de
rollout granular, namespaces) a costa de más archivos y comandos.

## Notas

- La imagen `traefik/whoami` es pública y sin costo, se usa solo para tener
  una respuesta HTTP que identifique al contenedor que la sirvió.
- El puerto `8000` (Swarm) y `8080` (Kubernetes) se usan a propósito para
  poder tener ambos entornos corriendo en paralelo sin conflicto de puertos.
