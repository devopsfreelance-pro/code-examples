# GitOps con Flux y ArgoCD: demo real con ArgoCD

Post: [Guía Completa de GitOps con Flux y ArgoCD](https://www.devopsfreelance.pro/blog/posts/gitops-con-flux-argocd/)

## Qué demuestra

El post compara Flux y ArgoCD, y en ambos casos el concepto central es el
mismo: declarás el estado deseado en Git (un `Application` de ArgoCD o una
`Kustomization` de Flux), y el operador GitOps sincroniza automáticamente
el cluster contra ese repo, sin que nadie corra `kubectl apply` a mano.

Este ejemplo instala **ArgoCD real** (no una simulación) en un cluster
`kind` local y despliega la app de ejemplo `guestbook` del propio proyecto
Argo, usando el mismo manifest `Application` que aparece en el post
(`syncPolicy.automated` con `prune` y `selfHeal`). Vas a ver:

1. ArgoCD levantándose en el cluster (server, repo-server, application
   controller, redis).
2. Una `Application` que apunta al repo público
   `https://github.com/argoproj/argocd-example-apps.git`, carpeta
   `guestbook`.
3. ArgoCD detectando esa `Application`, clonando el repo, y desplegando el
   Deployment + Service del guestbook automáticamente, sin ningún
   `kubectl apply` manual sobre esos recursos.
4. La app corriendo, accesible via port-forward.

No se toca Flux en este ejemplo porque instalar ambos operadores GitOps
completos en un mismo mini-lab sería redundante para el punto que
importa: el post ya incluye los YAML de instalación y configuración de
Flux (`flux bootstrap`, `GitRepository`, `Kustomization`) en la sección
"Configuración Práctica de Flux", que podés seguir igual con un cluster
`kind` si querés compararlo.

## Requisitos

- Docker (o Podman) corriendo localmente.
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) instalado.
- `kubectl` instalado.
- Conexión a internet (para bajar las imágenes de ArgoCD y clonar el repo
  público de ejemplo de Argo).

No se necesita cuenta de nube, token de Git ni credenciales: el repo que
usa la `Application` (`argocd-example-apps`) es público y de solo
lectura.

## Pasos

### 1. Dar permisos de ejecución a los scripts

```bash
chmod +x setup.sh cleanup.sh
```

### 2. Levantar todo (cluster + ArgoCD + Application via GitOps)

```bash
./setup.sh
```

Esto tarda unos minutos (bajar imágenes de ArgoCD y esperar a que
sincronice). Salida esperada (resumida):

```
==> Creando cluster kind 'gitops-argocd-demo'...
==> Instalando ArgoCD en el namespace 'argocd'...
==> Esperando a que los pods de ArgoCD esten listos...
==> Aplicando la Application 'guestbook' (esto dispara el sync GitOps)...
==> Esperando a que ArgoCD sincronice y despliegue 'guestbook'...
  intento 1: sync=OutOfSync health=Missing
  intento 2: sync=Synced health=Progressing
  intento 3: sync=Synced health=Healthy

==> Estado final de la Application:
NAME        SYNC STATUS   HEALTH STATUS
guestbook   Synced        Healthy

==> Pods desplegados via GitOps en el namespace 'guestbook':
NAME                           READY   STATUS    RESTARTS   AGE
guestbook-ui-xxxxxxxxx-yyyyy   1/1     Running   0          20s

==> Password inicial del admin de ArgoCD:
<password generado>

Listo. Para ver la app desplegada:
  kubectl port-forward svc/guestbook-ui -n guestbook 8081:80
  curl -s localhost:8081 | head -n 5

Para ver la UI de ArgoCD:
  kubectl port-forward svc/argocd-server -n argocd 8080:443
  usuario: admin / password: el impreso arriba
```

### 3. Ver la app desplegada por GitOps

```bash
kubectl port-forward svc/guestbook-ui -n guestbook 8081:80
```

En otra terminal:

```bash
curl -s localhost:8081 | head -n 5
```

Deberías ver el HTML de la SPA de ejemplo `guestbook` de Argo, servido
por un pod que nunca creaste con `kubectl apply` directo: lo creó ArgoCD
al leer el repo Git.

### 4. (Opcional) Ver la UI de ArgoCD

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Abrí `https://localhost:8080`, usuario `admin`, password el que imprimió
`setup.sh` (también podés obtenerlo de nuevo con):

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

### 5. Comprobar el self-heal (el punto central de GitOps)

Modificá manualmente el Deployment que gestiona ArgoCD, sin pasar por
Git:

```bash
kubectl scale deployment guestbook-ui -n guestbook --replicas=3
kubectl get pods -n guestbook
```

Vas a ver 3 pods brevemente. Como la `Application` tiene
`syncPolicy.automated.selfHeal: true`, ArgoCD detecta la divergencia
respecto al estado declarado en el repo (que no define 3 réplicas) y la
revierte:

```bash
sleep 20
kubectl get pods -n guestbook
```

Vuelve al número de réplicas que define el manifest en Git. Esto es
exactamente el comportamiento que el post describe como diferenciador de
GitOps frente a operar el cluster a mano.

### 6. Limpiar

```bash
./cleanup.sh
```

## Notas

- Se usa el manifest oficial de instalación completo de ArgoCD
  (`install.yaml`, incluye server, repo-server, redis, dex y
  application-controller), igual al que aparece en el post.
- El repo `argocd-example-apps` es mantenido por el proyecto Argo
  (`argoproj`), no requiere fork ni token: es el mismo repo público que
  usa la documentación oficial de ArgoCD y el propio post.
- Para probar Flux en lugar de ArgoCD, el post ya trae los comandos
  exactos (`flux bootstrap github ...`) y los manifests de
  `GitRepository`/`Kustomization`; solo hace falta un repo Git propio
  (Flux necesita poder escribir en él durante el bootstrap, a diferencia
  de ArgoCD que solo necesita lectura).
