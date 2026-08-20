# Multi-Cluster Kubernetes Management: mini-demo con kind

Post: [Multi-Cluster Kubernetes Management: Guía Práctica](https://www.devopsfreelance.pro/blog/posts/multi-cluster-kubernetes-management/)

## Qué demuestra este ejemplo

El post plantea la decisión hub-and-spoke vs gestión por flotas, y dos prácticas
que dependen de tener varios clusters: propagar una política de recursos
idéntica a toda la flota (sección "Consistencia de Configuración") y detectar
version skew antes de una ola de upgrades (sección "Estrategia de upgrades por
olas").

Este ejemplo levanta **dos clusters locales** (`region-us-east` y
`region-eu-west`) con [kind](https://kind.sigs.k8s.io/) para simular una flota
mínima, y luego:

1. Aplica la **misma** política (`ResourceQuota` + `LimitRange`, el
   equivalente real al `GlobalPolicy` de ejemplo del post) a los dos clusters
   con un solo comando, simulando el push de configuración GitOps de un
   modelo de flotas.
2. Verifica que la política quedó idéntica en ambos clusters (detección de
   drift trivial).
3. Lista la versión de control plane de cada cluster, el chequeo que harías
   antes de definir el orden de una ola de upgrades.

No monta un service mesh ni un control plane central real (Rancher, Fleet,
Karmada quedan fuera de alcance de un ejemplo local); el objetivo es que se
entienda, en minutos, la mecánica de "una config, muchos clusters" que está
detrás de cualquiera de esas herramientas.

## Requisitos

- Docker (o Podman) corriendo localmente.
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) instalado.
- `kubectl` instalado.
- `python3` (usado solo para parsear JSON en `check-version-skew.sh`).

No se necesita ninguna cuenta ni credencial de nube: todo corre en clusters
locales efímeros.

## Pasos para correrlo

```bash
cd multi-cluster-kubernetes-management

# 1. Levantar los dos clusters ("region-us-east" y "region-eu-west")
./create-clusters.sh

# 2. Propagar la política de recursos a toda la flota
./apply-to-all-clusters.sh

# 3. Chequear version skew entre clusters (previo a planificar una ola de upgrade)
./check-version-skew.sh

# 4. Limpiar todo al terminar
./cleanup.sh
```

## Salida esperada

`./create-clusters.sh`:

```
[create] cluster 'region-us-east'...
...
Clusters disponibles:
region-eu-west
region-us-east

Contextos kubectl generados:
kind-region-eu-west
kind-region-us-east
```

`./apply-to-all-clusters.sh`:

```
=== Aplicando politica en contexto: kind-region-eu-west ===
namespace/workloads created
resourcequota/resource-limits created
limitrange/resource-limits created
=== Aplicando politica en contexto: kind-region-us-east ===
namespace/workloads created
resourcequota/resource-limits created
limitrange/resource-limits created

=== Verificacion de consistencia entre clusters ===
--- kind-region-eu-west ---
{"limits.cpu":"4","limits.memory":"4Gi","pods":"20","requests.cpu":"2","requests.memory":"2Gi"}
--- kind-region-us-east ---
{"limits.cpu":"4","limits.memory":"4Gi","pods":"20","requests.cpu":"2","requests.memory":"2Gi"}
```

Los dos bloques JSON son idénticos: esa es la propiedad que un modelo de
flotas garantiza por diseño (todo sale del mismo Git), y que en hub-and-spoke
hay que reforzar con disciplina y auditoría.

`./check-version-skew.sh`:

```
CLUSTER                   VERSION SERVER
-------                   --------------
kind-region-eu-west       v1.31.0
kind-region-us-east       v1.31.0
```

(La versión exacta depende de la imagen de nodo que use tu instalación de
kind; lo relevante es que el script te da, de un vistazo, la lista que
necesitás antes de decidir con qué cluster arranca la ola de upgrade.)

## Archivos

- `create-clusters.sh` — crea los clusters kind de la demo.
- `policies/resource-limits.yaml` — política de recursos a propagar (namespace + ResourceQuota + LimitRange).
- `apply-to-all-clusters.sh` — aplica la política a todos los contextos `kind-*` y verifica consistencia.
- `check-version-skew.sh` — lista la versión de control plane de cada cluster de la flota.
- `cleanup.sh` — borra los clusters creados.
