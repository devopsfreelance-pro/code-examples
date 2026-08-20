# Gestión de usuarios y permisos a escala: RBAC de menor privilegio en Kubernetes

Post relacionado: [Gestión de Usuarios y Permisos a Escala - Guía Completa DevOps 2025](https://www.devopsfreelance.pro/blog/posts/gestion-usuarios-permisos-a-escala/)

## Qué demuestra este ejemplo

El post cubre muchas piezas de la gestión de identidades a escala (IAM de AWS,
Azure AD, LDAP, Vault, PAM, Zero Trust, etc.), pero el hilo conductor de todas
ellas es el mismo: **principio de menor privilegio + separación de
responsabilidades**, implementado en el post con el `ClusterRole`/`RoleBinding`
de RBAC de Kubernetes.

Este ejemplo toma esa parte concreta y la hace verificable en minutos: crea un
cluster Kubernetes local con `kind`, define dos roles con permisos distintos
(igual que "developers" vs. "security-team" en el post) y usa
`kubectl auth can-i --as` para comprobar, sin ambigüedad, que cada identidad
solo puede hacer lo que su rol le permite.

- `developer-sa`: puede leer/crear/actualizar `deployments` y leer `pods`,
  pero **no** puede borrar pods ni leer `secrets`.
- `security-sa`: puede leer `secrets` y `events` (auditoría), pero **no**
  puede crear `deployments` ni borrar `pods`.

Ambos roles están acotados al namespace `development` (scope mínimo posible),
tal como recomienda el post en "Segregación de Ambientes".

## Requisitos

- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/) (Kubernetes in Docker)
- `kubectl`
- Docker (o Podman) corriendo localmente

No se necesita cuenta de AWS/Azure ni ningún servicio pago: todo corre en un
cluster Kubernetes local de un solo nodo.

## Archivos

- `00-namespace-and-sa.yaml`: namespace `development` y dos `ServiceAccount`
  (`developer-sa`, `security-sa`) que representan a los dos usuarios de la demo.
- `01-rbac.yaml`: dos `ClusterRole` (`developer-role`, `security-role`) y sus
  `RoleBinding` correspondientes, acotados al namespace `development`.
- `test-rbac.sh`: crea el cluster kind, aplica los manifests y corre una
  batería de `kubectl auth can-i` para verificar que el RBAC funciona como
  se espera.

## Cómo correrlo

```bash
chmod +x test-rbac.sh
./test-rbac.sh
```

El script:

1. Crea (o reusa) un cluster kind llamado `rbac-demo`.
2. Aplica el namespace, los `ServiceAccount` y el RBAC.
3. Simula ser cada `ServiceAccount` con `kubectl auth can-i --as=...` y
   compara el resultado contra lo esperado.

## Salida esperada

```
==> Verificando permisos de 'developer-sa' (esperado: allow/deny mixto)
  [OK] can-i get      pods         -> yes (esperado: yes)
  [OK] can-i create   deployments  -> yes (esperado: yes)
  [OK] can-i delete   pods         -> no  (esperado: no)
  [OK] can-i get      secrets      -> no  (esperado: no)

==> Verificando permisos de 'security-sa'
  [OK] can-i get      secrets      -> yes (esperado: yes)
  [OK] can-i list     events       -> yes (esperado: yes)
  [OK] can-i create   deployments  -> no  (esperado: no)
  [OK] can-i delete   pods         -> no  (esperado: no)
```

Todas las líneas deben mostrar `[OK]`. Si alguna muestra `[FALLO]`, el RBAC
aplicado no coincide con la política esperada (útil para detectar
"permission drift" en un pipeline real de CI, tal como el stage
`verify_access` del pipeline de provisioning del post).

## Limpieza

```bash
kind delete cluster --name rbac-demo
```
