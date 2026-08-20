# Kyverno: native Kubernetes policies

Related post: [Kyverno Kubernetes Policies: The Complete Guide 2026](https://www.devopsfreelance.pro/blog/en/posts/kyverno-kubernetes-policies/)

## What this example demonstrates

The post presents the article's core validation policy (section
"Building Practical Policies"): a `ClusterPolicy` that requires every
Pod to define `resources.limits` for CPU and memory, rejecting at the
admission webhook any Pod that doesn't comply.

This example reproduces that flow end to end on a real, local Kubernetes
cluster (kind), without depending on any cloud provider:

1. `require-resource-limits.yaml` is the `ClusterPolicy` from the post
   (same rule, same `pattern`). The only change is
   `validationFailureAction` from `enforce` to `Enforce`: the post uses
   the old lowercase syntax, but current Kyverno versions (1.11+)
   require the capitalized value `Enforce`/`Audit`; lowercase makes the
   chart fail when installing the policy.
2. `pod-conforme.yaml` is a Pod with `limits` for CPU and memory
   defined: Kyverno should accept it.
3. `pod-no-conforme.yaml` is the same Pod without a `resources` block:
   Kyverno should reject it at `kubectl apply` time, with the message
   defined in the policy.
4. `run.sh` automates the whole thing: creates the kind cluster,
   installs Kyverno with Helm (the same commands from the post), applies
   the policy, and tests both Pods, verifying the result is as expected
   (one accepted, one rejected).

## Requirements

- Docker (or Podman) running, so kind can spin up the nodes
- [kind](https://kind.sigs.k8s.io/) (`go install sigs.k8s.io/kind@latest` or a release binary)
- `kubectl`
- `helm` v3

No cloud provider account is needed: everything runs locally.

## How to run it

```bash
cd kyverno-politicas-kubernetes
./run.sh
```

The script does, in order:

1. Creates (or reuses) a kind cluster named `kyverno-demo`.
2. Installs Kyverno in the `kyverno` namespace via Helm and waits for the
   pods to be `Ready`.
3. Applies `require-resource-limits.yaml` and waits for the policy to be
   ready (`status.ready == true`).
4. Creates the `demo-kyverno` namespace.
5. Applies `pod-conforme.yaml` (should be created without issues).
6. Applies `pod-no-conforme.yaml` (should be rejected by Kyverno's
   webhook).

## Expected output

```
== 6/6: probando los dos Pods ==

--- Pod CONFORME (tiene resources.limits): se espera que se cree ---
pod/pod-conforme created
OK: el pod conforme fue aceptado, como se esperaba.

--- Pod NO CONFORME (sin resources.limits): se espera que Kyverno lo rechace ---
OK: el admission webhook de Kyverno rechazo el Pod, como se esperaba:
  admission webhook "validate.kyverno.svc-fail" denied the request:

  resource Pod/demo-kyverno/pod-no-conforme was blocked due to the following policies

  require-resource-limits:
    check-container-resources: 'validation error: Todos los contenedores deben
      tener limites de CPU y memoria definidos. rule check-container-resources
      failed at path /spec/containers/0/resources/'

== Demo completada. Para limpiar: kind delete cluster --name kyverno-demo ==
```

(Note: the console output above comes directly from `run.sh`, which prints its own messages in Spanish; it is left unmodified since it is actual command output, not prose.)

## Manual verification (optional)

```bash
kubectl get clusterpolicy require-resource-limits
kubectl get pods -n demo-kyverno
kubectl describe clusterpolicy require-resource-limits   # ver status y estadisticas de la regla
```

## Cleanup

```bash
kind delete cluster --name kyverno-demo
```

---

## 🇪🇸 Versión en español

# Kyverno: políticas nativas de Kubernetes

Post relacionado: [Guía Completa de Kyverno para políticas en Kubernetes](https://www.devopsfreelance.pro/blog/posts/kyverno-politicas-kubernetes/)

## Qué demuestra este ejemplo

El post presenta la política de validación central del artículo (sección
"Creación de Políticas Prácticas"): una `ClusterPolicy` que exige que todo
Pod defina `resources.limits` de CPU y memoria, rechazando en el
admission webhook cualquier Pod que no cumpla.

Este ejemplo reproduce ese flujo de punta a punta en un cluster Kubernetes
real y local (kind), sin depender de ningún proveedor cloud:

1. `require-resource-limits.yaml` es la `ClusterPolicy` del post (misma
   regla, mismo `pattern`). Se ajustó únicamente `validationFailureAction`
   de `enforce` a `Enforce`: el post usa la sintaxis antigua en minúscula,
   pero las versiones actuales de Kyverno (1.11+) requieren el valor
   capitalizado `Enforce`/`Audit`; en minúscula el chart falla al instalar
   la policy.
2. `pod-conforme.yaml` es un Pod con `limits` de CPU y memoria definidos:
   Kyverno debe aceptarlo.
3. `pod-no-conforme.yaml` es el mismo Pod sin bloque `resources`: Kyverno
   debe rechazarlo en el momento del `kubectl apply`, con el mensaje
   definido en la policy.
4. `run.sh` automatiza todo: crea el cluster kind, instala Kyverno con
   Helm (los mismos comandos del post), aplica la policy, y prueba ambos
   Pods verificando que el resultado sea el esperado (uno aceptado, uno
   rechazado).

## Requisitos

- Docker (o Podman) corriendo, para que kind pueda levantar los nodos
- [kind](https://kind.sigs.k8s.io/) (`go install sigs.k8s.io/kind@latest` o binario de la release)
- `kubectl`
- `helm` v3

No hace falta cuenta de ningún cloud provider: todo corre localmente.

## Cómo correrlo

```bash
cd kyverno-politicas-kubernetes
./run.sh
```

El script hace, en orden:

1. Crea (o reutiliza) un cluster kind llamado `kyverno-demo`.
2. Instala Kyverno en el namespace `kyverno` vía Helm y espera a que los
   pods estén `Ready`.
3. Aplica `require-resource-limits.yaml` y espera a que la policy quede
   lista (`status.ready == true`).
4. Crea el namespace `demo-kyverno`.
5. Aplica `pod-conforme.yaml` (debe crearse sin problemas).
6. Aplica `pod-no-conforme.yaml` (debe ser rechazado por el webhook de
   Kyverno).

## Salida esperada

```
== 6/6: probando los dos Pods ==

--- Pod CONFORME (tiene resources.limits): se espera que se cree ---
pod/pod-conforme created
OK: el pod conforme fue aceptado, como se esperaba.

--- Pod NO CONFORME (sin resources.limits): se espera que Kyverno lo rechace ---
OK: el admission webhook de Kyverno rechazo el Pod, como se esperaba:
  admission webhook "validate.kyverno.svc-fail" denied the request:

  resource Pod/demo-kyverno/pod-no-conforme was blocked due to the following policies

  require-resource-limits:
    check-container-resources: 'validation error: Todos los contenedores deben
      tener limites de CPU y memoria definidos. rule check-container-resources
      failed at path /spec/containers/0/resources/'

== Demo completada. Para limpiar: kind delete cluster --name kyverno-demo ==
```

## Verificar manualmente (opcional)

```bash
kubectl get clusterpolicy require-resource-limits
kubectl get pods -n demo-kyverno
kubectl describe clusterpolicy require-resource-limits   # ver status y estadisticas de la regla
```

## Limpieza

```bash
kind delete cluster --name kyverno-demo
```
