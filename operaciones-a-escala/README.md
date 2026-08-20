# Operaciones a escala - ejemplos ejecutables

Post: [Guía Completa de Operaciones a escala](https://www.devopsfreelance.pro/blog/posts/operaciones-a-escala/)

Este directorio contiene dos mini-ejemplos que ilustran dos de los cinco
pilares que describe el post:

1. **Auto-scaling inteligente** (pilar "Eficiencia de Recursos" /
   "Automatización Extrema"): un `Deployment` + `HorizontalPodAutoscaler`
   real que escala pods automáticamente al recibir carga, corriendo en un
   cluster local `kind`.
2. **Circuit Breaker** (pilar "Resiliencia por Diseño"): un script Python
   standalone que reproduce el patrón de circuit breaker del post (Go) para
   evitar cascading failures cuando una dependencia falla.

No se necesita ninguna cuenta ni servicio pago: todo corre en local.

## Requisitos

- Docker
- [kind](https://kind.sigs.k8s.io/) (Kubernetes in Docker)
- kubectl
- Python 3.8+ (solo para el ejemplo de circuit breaker, sin dependencias externas)

## Parte 1: HPA autoscaling en kind

### 1. Crear el cluster local

```bash
kind create cluster --name ops-a-escala
```

### 2. Instalar metrics-server (necesario para que el HPA lea CPU)

kind no trae metrics-server. Se instala con el manifest oficial y se
desactiva la verificación TLS de kubelet (solo válido para clusters
locales de prueba):

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl patch deployment metrics-server -n kube-system --type=json \
  -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
```

Esperar a que esté listo:

```bash
kubectl rollout status deployment/metrics-server -n kube-system --timeout=120s
```

### 3. Desplegar el servicio de ejemplo y el HPA

```bash
kubectl apply -f k8s/deployment.yaml
```

Verificar que el pod esté `Running` y el HPA esté leyendo métricas
(puede tardar 1-2 minutos en mostrar `%CPU` en vez de `<unknown>`):

```bash
kubectl get deployment echo-service
kubectl get hpa echo-service-hpa --watch
```

### 4. Generar carga y ver el autoscaling en acción

En otra terminal, dejar el `watch` del HPA corriendo y ejecutar:

```bash
chmod +x scripts/load-test.sh
./scripts/load-test.sh default 180
```

### Salida esperada

En la terminal del `watch` del HPA se debe ver cómo `REPLICAS` sube desde
1 hacia el `maxReplicas: 6` a medida que `TARGETS` (CPU actual vs 50%
configurado) supera el umbral, y luego baja de nuevo al terminar la carga:

```
NAME               REFERENCE                 TARGETS         MINPODS   MAXPODS   REPLICAS
echo-service-hpa   Deployment/echo-service    12%/50%         1         6         1
echo-service-hpa   Deployment/echo-service    180%/50%        1         6         4
echo-service-hpa   Deployment/echo-service    95%/50%         1         6         6
echo-service-hpa   Deployment/echo-service    8%/50%          1         6         1
```

### 5. Limpiar

```bash
kind delete cluster --name ops-a-escala
```

## Parte 2: Circuit Breaker

No requiere cluster ni dependencias, solo Python estándar:

```bash
python3 scripts/circuit_breaker.py
```

### Salida esperada

El script simula 20 llamadas a un servicio downstream que falla el 60% de
las veces. Se debe ver cómo, tras 3 fallos consecutivos, el circuito pasa
a `OPEN` y rechaza llamadas sin siquiera intentarlas (evitando saturar el
servicio caído), y cómo tras el `reset_timeout` pasa a `HALF_OPEN` para
probar de nuevo:

```
[01] estado=CLOSED    -> exito: 200 OK
[02] estado=CLOSED    -> fallo: downstream service timeout
[03] estado=CLOSED    -> fallo: downstream service timeout
[04] estado=CLOSED    -> fallo: downstream service timeout
[05] estado=OPEN      -> rechazado: circuit breaker abierto: llamada rechazada
[06] estado=OPEN      -> rechazado: circuit breaker abierto: llamada rechazada
[07] estado=HALF_OPEN -> exito: 200 OK
...
```

(Los resultados exactos varían porque las fallas del servicio simulado son
aleatorias.)

## Archivos

- `k8s/deployment.yaml`: Deployment + Service + HorizontalPodAutoscaler
- `scripts/load-test.sh`: genera carga concurrente contra el servicio desde un pod temporal
- `scripts/circuit_breaker.py`: implementación standalone del patrón circuit breaker
