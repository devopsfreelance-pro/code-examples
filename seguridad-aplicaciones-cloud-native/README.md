# Seguridad en aplicaciones cloud-native: demo de Pod Security Admission + NetworkPolicy

Post relacionado: [Guía Completa de Seguridad en aplicaciones cloud-native](https://www.devopsfreelance.pro/blog/posts/seguridad-aplicaciones-cloud-native/)

## Qué demuestra este ejemplo

El post explica varios controles de seguridad para Kubernetes (security contexts,
políticas de admisión con Kyverno, NetworkPolicies, RBAC). Este ejemplo se enfoca
en la parte que se puede reproducir en minutos sin instalar nada externo: el
**Pod Security Admission** (PSA), un controlador de admisión nativo de Kubernetes
(reemplazo built-in de los antiguos PodSecurityPolicies) que aplica el mismo
principio que Kyverno en el post pero sin requerir instalar un operador aparte.

Se crea un namespace con el perfil `restricted` y se despliegan dos pods:

- `insecure-pod.yaml`: sin `securityContext`, corre como root, sin restricciones.
  El API server debe **rechazarlo**.
- `secure-pod.yaml`: cumple los requisitos de `restricted` (usuario no root,
  `readOnlyRootFilesystem`, `capabilities: drop: [ALL]`, `seccompProfile:
  RuntimeDefault`, `allowPrivilegeEscalation: false`) igual que el ejemplo de
  Security Context del post. El API server debe **aceptarlo**.

Además se aplica `network-policy.yaml`, la NetworkPolicy de microsegmentación
del post (principio Zero Trust), para mostrar la sintaxis declarativa de
restricción de tráfico a nivel de pod.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/) (o Podman) corriendo localmente
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) (Kubernetes in Docker)
- [kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl)

No hace falta ninguna cuenta ni servicio de pago: todo corre en un cluster
Kubernetes local dentro de contenedores Docker.

## Pasos para ejecutar

```bash
# 1. Dar permisos de ejecución al script (si no los tiene ya)
chmod +x deploy.sh

# 2. Ejecutar la demo completa (crea el cluster kind si no existe)
./deploy.sh
```

El script hace, en orden:

1. Crea (o reutiliza) un cluster kind llamado `secure-demo`.
2. Aplica el namespace `secure-demo` con la etiqueta
   `pod-security.kubernetes.io/enforce: restricted`.
3. Intenta aplicar `insecure-pod.yaml` -> debe fallar con un error de admisión.
4. Aplica `secure-pod.yaml` -> debe crearse y llegar a estado `Ready`.
5. Aplica la `NetworkPolicy` de microsegmentación.
6. Muestra el estado final de los pods y la policy.

## Salida esperada

Al correr `./deploy.sh` vas a ver algo como esto (resumido):

```
==> Intentando desplegar el Pod INSEGURO (se espera RECHAZO)...
Error from server (Forbidden): error when creating "insecure-pod.yaml":
pods "insecure-app" is forbidden: violates PodSecurity "restricted:latest":
allowPrivilegeEscalation != false (container "app" must set
securityContext.allowPrivilegeEscalation=false), unrestricted capabilities
(container "app" must set securityContext.capabilities.drop=["ALL"]),
runAsNonRoot != true (pod or container "app" must set
securityContext.runAsNonRoot=true), seccompProfile (pod or container "app"
must set securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")
OK: el API server rechazo el pod inseguro, tal como se espera.

==> Desplegando el Pod SEGURO (se espera ACEPTACION)...
pod/secure-app created
==> Esperando a que el pod seguro este Ready...
pod/secure-app condition met

==> Estado final:
NAME         READY   STATUS    RESTARTS   AGE
secure-app   1/1     Running   0          15s

NAME                        POD-SELECTOR      AGE
secure-app-network-policy   app=secure-app    2s
```

## Verificar manualmente

```bash
# Ver por qué fue rechazado el pod inseguro (si querés repetir el intento)
kubectl apply -f insecure-pod.yaml

# Inspeccionar el security context aplicado al pod seguro
kubectl get pod secure-app -n secure-demo -o jsonpath='{.spec.securityContext}'

# Ver la NetworkPolicy aplicada
kubectl describe networkpolicy secure-app-network-policy -n secure-demo
```

## Nota sobre la NetworkPolicy

El CNI por defecto de kind (`kindnet`) **no aplica** (no enforce-a) las
NetworkPolicies, aunque `kubectl apply` las acepte sin error. Este ejemplo
incluye el manifest para mostrar la sintaxis y dejarlo declarado en el
cluster; para verificar el bloqueo de tráfico real hace falta un CNI que
sí las implemente, como [Calico](https://docs.tigera.io/calico/latest/getting-started/kubernetes/kind)
o [Cilium](https://docs.cilium.io/en/stable/gettingstarted/kind/). El
Pod Security Admission, en cambio, sí se aplica siempre porque es parte
del propio API server de Kubernetes.

## Limpieza

```bash
kind delete cluster --name secure-demo
```
