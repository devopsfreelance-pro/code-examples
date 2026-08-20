# Compliance as Code: bloqueo preventivo de manifiestos inseguros con OPA

Post relacionado: [Guía Completa de Compliance as Code](https://www.devopsfreelance.pro/blog/posts/compliance-as-code/)

## Qué demuestra este ejemplo

El post explica que el compliance as code convierte requisitos de seguridad
en código ejecutable que verifica automáticamente cada cambio antes de que
llegue a producción (sección "Policy as Code: El Corazón del Sistema"),
usando como ejemplo una política de Open Policy Agent (OPA) que exige que
los contenedores de Kubernetes corran como usuario no-root y sin modo
privilegiado.

Este ejemplo reproduce esa política de forma 100% local, sin necesitar un
clúster de Kubernetes ni un admission controller real:

1. `policies/kubernetes-security.rego` contiene las dos reglas `deny` del
   post (no-root obligatorio, sin modo privilegiado), adaptadas para recibir
   el manifiesto YAML crudo en vez del payload de un `AdmissionReview`.
2. `manifests/pod-compliant.yaml` y `manifests/pod-noncompliant.yaml` son
   dos Pods de ejemplo: uno cumple la política, el otro corre como root y en
   modo privilegiado.
3. `validate.sh` corre `conftest` (el motor que ejecuta políticas Rego
   contra archivos de configuración) sobre ambos manifiestos, igual que un
   paso de CI/CD que bloquea un merge o un deploy. El script termina con
   `exit 1` si el manifiesto inseguro no es rechazado, y `exit 0` si la
   política funciona como se espera.

Esto ilustra el principio central del post: "shift left" del compliance,
detectando violaciones de políticas en el pipeline en vez de auditar
manualmente la infraestructura después del hecho.

## Requisitos

Una de las dos opciones:

- **Opción A (recomendada, sin instalar nada):** Docker. El script usa la
  imagen `openpolicyagent/conftest` automáticamente si no encuentra el
  binario `conftest` instalado.
- **Opción B:** [conftest](https://www.conftest.dev/install/) instalado
  localmente (`brew install conftest`, o binario desde GitHub releases).

No hace falta Kubernetes, kind, minikube ni ninguna cuenta cloud.

## Cómo correrlo

```bash
cd compliance-as-code
./validate.sh
```

## Salida esperada

```
== Compliance as code: validando manifiestos de Kubernetes contra policies/kubernetes-security.rego ==

--- Caso 1: pod compliant (se espera PASS) ---

2 tests, 2 passed, 0 warnings, 0 failures, 0 exceptions

--- Caso 2: pod NO compliant (se espera FAIL) ---
FAIL - manifests/pod-noncompliant.yaml - main - El contenedor 'debug' debe ejecutarse como usuario no-root (securityContext.runAsNonRoot: true)
FAIL - manifests/pod-noncompliant.yaml - main - El contenedor 'debug' no puede ejecutarse en modo privilegiado (securityContext.privileged: true)

2 tests, 0 passed, 0 warnings, 2 failures, 0 exceptions

== Resultado: la política bloqueó correctamente el manifiesto inseguro (exit code 1) ==
```

El Pod `pod-compliant.yaml` (imagen no-root, sin privilegios) pasa las dos
reglas. El Pod `pod-noncompliant.yaml` (sin `runAsNonRoot`, con
`privileged: true`) dispara ambas violaciones, tal como lo haría un
admission controller real bloqueando el `kubectl apply` en un clúster
productivo.

## Ir más allá

Para probar la política contra tus propios manifiestos:

```bash
conftest test tu-manifiesto.yaml --policy policies
```

Para simular el uso real como admission controller, herramientas como
[Gatekeeper](https://open-policy-agent.github.io/gatekeeper/) o
[Kyverno](https://kyverno.io/) cargan políticas equivalentes directamente en
el clúster y rechazan los `kubectl apply` que las violen, en vez de
validarlas como paso separado de CI/CD.
