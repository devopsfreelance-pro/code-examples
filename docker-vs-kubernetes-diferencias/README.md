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
