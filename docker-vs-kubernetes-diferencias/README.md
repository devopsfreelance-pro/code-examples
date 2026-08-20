# Docker vs Kubernetes: self-healing and scaling in practice

Related post: [Docker vs Kubernetes: Differences and When to Use Each](https://www.devopsfreelance.pro/blog/en/posts/docker-vs-kubernetes-differences/)

## What this example demonstrates

The post explains that Docker builds and runs containers, while Kubernetes orchestrates them (restarts, scales, load-balances). This example makes it tangible with the same application (an `nginx` serving a static page) deployed two ways:

1. **Docker alone** (`docker-compose.yml`): if you kill the container, it stays dead. There's no auto-healing.
2. **Kubernetes** (`k8s/`): if you kill a pod, the Deployment recreates it on its own. You can also scale replicas with a single command, something Docker Compose doesn't offer natively.

## Requirements

- Docker (with Docker Compose v2, `docker compose`)
- [kind](https://kind.sigs.k8s.io/) and `kubectl` (for the Kubernetes part)

## Part 1: Docker alone (no auto-healing)

```bash
cd docker-vs-kubernetes-diferencias

# Levantar el contenedor
docker compose up -d

# Verificar que responde
curl http://localhost:8080
# Esperado: HTML con "Hola desde el contenedor"

# Simular una caída
docker kill docker-demo-web

# Verificar que sigue caído (Docker no lo reinicia por sí solo)
docker ps -a --filter name=docker-demo-web
# Esperado: STATUS "Exited (137)..."

# Limpiar
docker compose down
```

## Part 2: Kubernetes (with auto-healing and scaling)

```bash
cd docker-vs-kubernetes-diferencias

# Crear un cluster local con kind (si no existe uno)
kind create cluster --name docker-vs-k8s-demo

# Desplegar la app
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Ver que hay 2 réplicas corriendo
kubectl get pods -l app=k8s-demo-web
# Esperado: 2 pods en estado Running

# Simular una caída: borrar un pod
POD=$(kubectl get pods -l app=k8s-demo-web -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod "$POD"

# Verificar auto-healing: Kubernetes crea un pod nuevo para mantener las 2 réplicas
kubectl get pods -l app=k8s-demo-web
# Esperado: sigue habiendo 2 pods (uno nuevo con AGE reciente reemplazando al borrado)

# Escalar a 5 réplicas con un solo comando
kubectl scale deployment/k8s-demo-web --replicas=5
kubectl get pods -l app=k8s-demo-web
# Esperado: 5 pods en estado Running

# Probar el servicio desde dentro del cluster
kubectl run curl-test --rm -it --restart=Never --image=curlimages/curl -- \
  curl -s http://k8s-demo-web
# Esperado: HTML con "Hola desde Kubernetes"

# Limpiar
kubectl delete -f k8s/service.yaml -f k8s/deployment.yaml -f k8s/configmap.yaml
kind delete cluster --name docker-vs-k8s-demo
```

## Expected output (summary)

- With **Docker alone**: killing the container leaves it `Exited` until someone restarts it manually.
- With **Kubernetes**: deleting a pod causes the Deployment to replace it automatically to maintain the declared replica count (`replicas: 2`), and scaling is a single command (`kubectl scale`).

This difference is exactly the central point of the post: Docker runs containers, Kubernetes keeps them alive and scaled as declared.

## Files

- `docker-compose.yml`: runs an `nginx` serving `app/index.html` (plain Docker, no orchestration).
- `app/index.html`: content served by the Docker part.
- `k8s/configmap.yaml`: HTML content served by the Kubernetes part.
- `k8s/deployment.yaml`: Deployment with 2 replicas, resource requests/limits.
- `k8s/service.yaml`: ClusterIP Service that exposes the Deployment inside the cluster.

---

## 🇪🇸 Versión en español

# Docker vs Kubernetes: self-healing y escalado en la práctica

Post relacionado: [Docker vs Kubernetes: Diferencias, Cuándo Usar Cada Uno y Cómo se Complementan](https://www.devopsfreelance.pro/blog/posts/docker-vs-kubernetes-diferencias/)

## Qué demuestra este ejemplo

El post explica que Docker crea y ejecuta contenedores, mientras que Kubernetes los orquesta (reinicia, escala, balancea). Este ejemplo lo hace tangible con la misma aplicación (un `nginx` sirviendo una página estática) desplegada de dos formas:

1. **Solo Docker** (`docker-compose.yml`): si matás el contenedor, se queda muerto. No hay auto-healing.
2. **Kubernetes** (`k8s/`): si matás un pod, el Deployment lo recrea solo. Además se puede escalar réplicas con un comando, algo que Docker Compose no ofrece de forma nativa.

## Requisitos

- Docker (con Docker Compose v2, `docker compose`)
- [kind](https://kind.sigs.k8s.io/) y `kubectl` (para la parte de Kubernetes)

## Parte 1: Solo Docker (sin auto-healing)

```bash
cd docker-vs-kubernetes-diferencias

# Levantar el contenedor
docker compose up -d

# Verificar que responde
curl http://localhost:8080
# Esperado: HTML con "Hola desde el contenedor"

# Simular una caída
docker kill docker-demo-web

# Verificar que sigue caído (Docker no lo reinicia por sí solo)
docker ps -a --filter name=docker-demo-web
# Esperado: STATUS "Exited (137)..."

# Limpiar
docker compose down
```

## Parte 2: Kubernetes (con auto-healing y escalado)

```bash
cd docker-vs-kubernetes-diferencias

# Crear un cluster local con kind (si no existe uno)
kind create cluster --name docker-vs-k8s-demo

# Desplegar la app
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Ver que hay 2 réplicas corriendo
kubectl get pods -l app=k8s-demo-web
# Esperado: 2 pods en estado Running

# Simular una caída: borrar un pod
POD=$(kubectl get pods -l app=k8s-demo-web -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod "$POD"

# Verificar auto-healing: Kubernetes crea un pod nuevo para mantener las 2 réplicas
kubectl get pods -l app=k8s-demo-web
# Esperado: sigue habiendo 2 pods (uno nuevo con AGE reciente reemplazando al borrado)

# Escalar a 5 réplicas con un solo comando
kubectl scale deployment/k8s-demo-web --replicas=5
kubectl get pods -l app=k8s-demo-web
# Esperado: 5 pods en estado Running

# Probar el servicio desde dentro del cluster
kubectl run curl-test --rm -it --restart=Never --image=curlimages/curl -- \
  curl -s http://k8s-demo-web
# Esperado: HTML con "Hola desde Kubernetes"

# Limpiar
kubectl delete -f k8s/service.yaml -f k8s/deployment.yaml -f k8s/configmap.yaml
kind delete cluster --name docker-vs-k8s-demo
```

## Salida esperada (resumen)

- Con **Docker solo**: al matar el contenedor, queda `Exited` hasta que alguien lo reinicie manualmente.
- Con **Kubernetes**: al borrar un pod, el Deployment lo reemplaza automáticamente para mantener el número de réplicas declarado (`replicas: 2`), y escalar es un solo comando (`kubectl scale`).

Esta diferencia es exactamente el punto central del post: Docker ejecuta contenedores, Kubernetes los mantiene vivos y escalados según lo declarado.

## Archivos

- `docker-compose.yml`: levanta un `nginx` sirviendo `app/index.html` (Docker puro, sin orquestación).
- `app/index.html`: contenido servido por la parte de Docker.
- `k8s/configmap.yaml`: contenido HTML servido por la parte de Kubernetes.
- `k8s/deployment.yaml`: Deployment con 2 réplicas, resource requests/limits.
- `k8s/service.yaml`: Service ClusterIP que expone el Deployment dentro del cluster.
