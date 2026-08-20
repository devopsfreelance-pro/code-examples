# Chaos Engineering: experimento de pod-termination en Kubernetes

Ejemplo de código para el post [Guía Completa de Chaos Engineering](https://www.devopsfreelance.pro/blog/posts/chaos-engineering/).

## Qué demuestra

El post incluye un experimento conceptual en YAML (hipótesis, steady-state,
método y rollback). Este ejemplo lo convierte en algo ejecutable: un script
que aplica el método científico del chaos engineering contra un `Deployment`
real en Kubernetes, sin depender de plataformas comerciales (Gremlin) ni de
operadores pesados (LitmusChaos, Chaos Mesh):

1. Despliega `checkout-service` con 5 réplicas (steady-state inicial).
2. Mide disponibilidad en tiempo real haciendo requests HTTP cada segundo.
3. Termina 2 de los 5 pods cada 15 segundos (el "ataque").
4. Si la disponibilidad cae por debajo del 95%, dispara un **rollback**
   automático y aborta el experimento — igual que la condición
   `availability < 95% -> stop-experiment` del YAML del post.
5. Al final, confirma o rechaza la hipótesis ("disponibilidad >99.9% con
   2 de 5 pods caídos") con datos reales.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/)
- [kind](https://kind.sigs.k8s.io/) (Kubernetes in Docker)
- `kubectl`
- `bc` y `shuf` (coreutils, vienen por defecto en la mayoría de distros Linux/WSL)

No se necesita cuenta ni servicio pago: todo corre en un cluster local.

## Pasos

```bash
# 1. Crear un cluster local con kind (si no tenés uno)
kind create cluster --name chaos-demo

# 2. Verificar que kubectl apunta al cluster correcto
kubectl cluster-info --context kind-chaos-demo

# 3. Dar permisos de ejecución y correr el experimento
cd chaos-engineering
chmod +x run-chaos-experiment.sh
./run-chaos-experiment.sh
```

El script tarda aproximadamente 1 minuto en correr (duración configurable
con la variable `EXPERIMENT_DURATION` dentro del script).

### Limpieza

```bash
kubectl delete namespace chaos-demo
kind delete cluster --name chaos-demo
```

## Salida esperada

Con `nginx` como carga de trabajo, el `Deployment` con 5 réplicas suele
absorber la pérdida de 2 pods sin caídas de disponibilidad relevantes
(Kubernetes reprograma los pods terminados casi de inmediato), por lo que
lo normal es ver la hipótesis **confirmada**:

```
== Chaos Engineering demo: pod-termination-checkout-service ==

Hipótesis: checkout-service mantiene disponibilidad >99.9% con 2 de 5 pods terminados

1) Aplicando manifiestos (namespace + deployment + service)...
namespace/chaos-demo created
deployment.apps/checkout-service created
service/checkout-service created

2) Esperando steady-state inicial (rollout de 5 réplicas listas)...
deployment "checkout-service" successfully rolled out

3) Abriendo port-forward hacia el servicio (localhost:8080)...

4) Iniciando monitor de disponibilidad (1 request/seg, log en /tmp/tmp.XXXXXX)...

5) Método: terminando 2 pods cada 15s durante 60s...

>> t=15s: terminando pods:
     pod/checkout-service-7b9f8c6d4-abcde
     pod/checkout-service-7b9f8c6d4-fghij
   disponibilidad acumulada: 100.00%
>> t=30s: terminando pods:
     pod/checkout-service-7b9f8c6d4-klmno
     pod/checkout-service-7b9f8c6d4-pqrst
   disponibilidad acumulada: 100.00%
>> t=45s: terminando pods:
     pod/checkout-service-7b9f8c6d4-uvwxy
     pod/checkout-service-7b9f8c6d4-zabcd
   disponibilidad acumulada: 100.00%
>> t=60s: terminando pods:
     pod/checkout-service-7b9f8c6d4-efghi
     pod/checkout-service-7b9f8c6d4-jklmn
   disponibilidad acumulada: 100.00%

== Resultado del experimento ==
Disponibilidad medida: 100.00%
Estado: completado
Hipótesis: CONFIRMADA — disponibilidad >= 99.9% con pods terminados
```

Si el port-forward llega a saturarse durante una terminación (dependiendo
de la velocidad del scheduler y del hardware local), vas a ver algún `0`
en el log y una disponibilidad ligeramente menor a 100% — eso también es
un resultado válido del experimento, y es exactamente el tipo de señal que
el chaos engineering busca exponer antes de que ocurra en producción.

## Archivos

- `k8s/checkout-service.yaml` — Namespace, Deployment (5 réplicas de nginx)
  y Service que representan el "checkout-service" del ejemplo del post.
- `run-chaos-experiment.sh` — Script que ejecuta el experimento completo:
  steady-state, ataque (pod-termination), monitoreo y rollback condicional.
