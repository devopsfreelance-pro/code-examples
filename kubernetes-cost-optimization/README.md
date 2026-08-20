# Kubernetes Cost Optimization: ejemplo práctico con kind

Post relacionado: [Guía Completa de Kubernetes cost optimization](https://www.devopsfreelance.pro/blog/posts/kubernetes-cost-optimization/)

## Qué demuestra este ejemplo

El post cubre varias estrategias (right-sizing, spot instances, Karpenter,
ResourceQuotas, Kubecost/OpenCost). Reproducir spot instances o Karpenter
localmente no es viable sin una cuenta cloud, así que este ejemplo aterriza el
concepto con mayor impacto inmediato del post -**right-sizing**- con
herramientas 100% locales y gratuitas:

- Levanta un cluster Kubernetes local con `kind` e instala `metrics-server`.
- Despliega un `Deployment` deliberadamente **sobredimensionado**: pide
  `1 CPU / 1Gi` por pod para correr un `nginx` casi en reposo, el mismo
  escenario de "pod que pide 1 CPU y 2Gi pero usa 200m y 400Mi" que describe
  la sección "El problema del sobreaprovisionamiento" del post.
- Despliega una `ResourceQuota` de namespace, igual a la del post, para
  mostrar cómo se limita el consumo total de un equipo.
- Corre un script que compara los `requests` declarados contra el consumo
  real medido por `metrics-server` (equivalente local del chequeo que el post
  hace con la query PromQL `container_cpu_usage_seconds_total /
  kube_pod_container_resource_requests`), para decidir si conviene bajar los
  requests.

No incluye Karpenter, spot instances, VPA ni Kubecost/OpenCost (esas partes
requieren un cloud provider real o instalar herramientas adicionales); se
enfoca en el flujo mínimo real de "medir uso real vs. lo reservado" que es la
base de toda optimización de costos en Kubernetes.

## Requisitos

- Docker (o Podman) corriendo localmente
- [kind](https://kind.sigs.k8s.io/) >= 0.20 (`kind version`)
- `kubectl` >= 1.26
- Python 3 (usado solo para formatear la salida de `kubectl get pods -o json`)
- Bash

Instalación rápida de kind (Linux):

```bash
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.23.0/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind
```

## Estructura

```
kubernetes-cost-optimization/
├── kind/
│   └── cluster.yaml              # config kind: control-plane + 1 worker
├── manifests/
│   └── app.yaml                  # Namespace + ResourceQuota + Deployment sobredimensionado
└── scripts/
    ├── setup.sh                  # crea el cluster, instala metrics-server, despliega
    ├── check-rightsizing.sh      # compara requests declarados vs uso real
    └── cleanup.sh                # borra el cluster
```

## Pasos para correrlo

Desde el directorio `kubernetes-cost-optimization/`:

```bash
# 1. Crear el cluster, instalar metrics-server y desplegar el demo
#    (tarda 2-4 minutos: descarga imagenes de kind, metrics-server y nginx)
./scripts/setup.sh

# 2. Comparar requests declarados vs consumo real
./scripts/check-rightsizing.sh

# 3. (Opcional) Ver la ResourceQuota aplicada al namespace
kubectl describe resourcequota team-backend-quota -n cost-demo

# 4. Limpiar todo al terminar
./scripts/cleanup.sh
```

## Salida esperada

Tras `setup.sh`, al final:

```
deployment "api-catalogo" successfully rolled out

Listo. Corre ./scripts/check-rightsizing.sh para ver requests vs uso real.
```

Tras `check-rightsizing.sh`:

```
=== Requests declarados (resources.requests) ===
api-catalogo-6d8f9c9c7f-abcde   cpu_request=1000m       mem_request=1Gi
api-catalogo-6d8f9c9c7f-fghij   cpu_request=1000m       mem_request=1Gi

=== Esperando metricas reales de metrics-server (puede tardar ~30-60s) ===

=== Uso real (kubectl top pods) ===
NAME                            CPU(cores)   MEMORY(bytes)
api-catalogo-6d8f9c9c7f-abcde   2m           9Mi
api-catalogo-6d8f9c9c7f-fghij   2m           8Mi

=== Conclusion ===
Compara CPU(cores)/MEMORY(bytes) de 'kubectl top' contra los requests de
arriba: si el uso real esta muy por debajo del request (ratio < 0.5, la
regla del post), el Deployment esta sobredimensionado. En este demo,
api-catalogo pide 1 CPU / 1Gi por pod pero nginxdemos/hello en reposo usa
apenas unos mCPU y ~10-20Mi: es exactamente el caso que 'Right-sizing'
describe en el post.
```

(los valores exactos de CPU/memoria dependen de tu máquina; lo relevante es
que el uso real queda muy por debajo de los requests declarados).

## Notas

- No se usan credenciales ni cuentas cloud: todo corre en contenedores
  locales vía kind.
- La imagen `nginxdemos/hello` es pública y gratuita, solo para tener un
  proceso real corriendo dentro del pod.
- `setup.sh` parchea `metrics-server` con `--kubelet-insecure-tls` porque
  kind usa certificados de kubelet self-signed; en un cluster EKS/GKE real no
  hace falta ese flag.
- Con los datos de `check-rightsizing.sh` en mano, el siguiente paso natural
  (no incluido aquí) es bajar los `requests` del `manifests/app.yaml` a algo
  cercano al uso real observado, tal como recomienda el post.
