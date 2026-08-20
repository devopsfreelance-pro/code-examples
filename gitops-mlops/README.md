# GitOps para MLOps - Mini demo ejecutable

Post relacionado: [GitOps para MLOps - Automatización de Modelos ML](https://www.devopsfreelance.pro/blog/posts/gitops-mlops/)

## Qué demuestra este ejemplo

El post explica GitOps para MLOps usando Flux/ArgoCD como "operadores de
sincronización" que reconcilian el cluster contra un repositorio Git que
actúa como fuente de verdad. Instalar Flux o ArgoCD completos no es viable
en un mini-ejemplo, así que esta demo implementa la misma idea central en
miniatura:

- `manifests/model-server.yaml` define un "modelo servido" (un Deployment +
  Service de Kubernetes) como código versionado.
- `scripts/gitops-controller.sh` es un mini-operador de reconciliación: vigila
  un repositorio Git local y, cada vez que detecta un commit nuevo, aplica
  automáticamente `manifests/` al cluster con `kubectl apply`. Es exactamente
  el loop que hacen Flux/ArgoCD, reducido a su esencia.
- `scripts/demo.sh` orquesta todo: crea el cluster, inicializa el repo Git
  "source of truth", arranca el controlador, y simula un despliegue nuevo de
  modelo (`v1.0.0 -> v2.0.0`) haciendo un commit. Vas a ver cómo el cluster se
  actualiza solo, sin tocar `kubectl` a mano después del primer despliegue.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/) corriendo localmente.
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/) (Kubernetes in Docker).
- `kubectl`.
- `git` y `bash` (ya vienen en Linux/macOS).

No se usan servicios pagos ni cuentas externas: todo corre en un cluster kind
local y un repo Git local (no hace falta GitHub).

## Cómo correrlo

```bash
cd gitops-mlops
chmod +x scripts/*.sh
./scripts/demo.sh
```

El script:

1. Crea el cluster `mlops-gitops-demo` con kind (si ya existe, lo reutiliza).
2. Crea un repo Git temporal con `manifests/model-server.yaml` adentro y hace
   el commit inicial (`modelo v1.0.0`).
3. Lanza `gitops-controller.sh` en background: aplica el estado inicial al
   namespace `mlops-demo`.
4. Espera 10s y muestra `kubectl get deployment,pods,svc`.
5. Modifica el manifest (`v1.0.0 -> v2.0.0`) y hace un nuevo commit, simulando
   que alguien mergeó un cambio en el repo GitOps.
6. Espera 10s a que el controlador detecte el commit nuevo y reconcilie solo.
7. Verifica con un pod `curl` efímero qué versión de modelo está sirviendo el
   Service.
8. Al terminar (Ctrl+C o fin del script), detiene el controlador. El cluster
   kind queda arriba para que sigas jugando.

Para borrar el cluster al terminar:

```bash
kind delete cluster --name mlops-gitops-demo
```

## Salida esperada

Primer `kubectl get` (después del commit inicial):

```
NAME                                    READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/ml-model-server         1/1     1            1           10s

NAME                                READY   STATUS    RESTARTS   AGE
pod/ml-model-server-xxxxxxxxx-xxxxx   1/1     Running   0          10s

NAME                          TYPE        CLUSTER-IP     PORT(S)   AGE
service/ml-model-server       ClusterIP   10.x.x.x       80/TCP    10s
```

Segundo `kubectl get` (después del commit con `v2.0.0`), el Deployment se
actualiza solo sin intervención manual (los pods se recrean por el cambio en
el spec del contenedor):

```
NAME                                    READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/ml-model-server         1/1     1            1           25s
```

Y la verificación final con `curl`:

```
modelo-recomendacion v2.0.0
```

Eso confirma el punto central del post: el repo Git es la fuente de verdad,
y un cambio committeado ahí (no un `kubectl apply` manual) es lo que dispara
el nuevo estado en el cluster.

## Correr el controlador manualmente (sin demo.sh)

Si querés inspeccionar el loop de reconciliación paso a paso:

```bash
kind create cluster --name mlops-gitops-demo
mkdir -p /tmp/gitops-repo/manifests
cp manifests/model-server.yaml /tmp/gitops-repo/manifests/
git -C /tmp/gitops-repo init
git -C /tmp/gitops-repo add manifests/
git -C /tmp/gitops-repo -c user.email=demo@example.com -c user.name=demo commit -m "estado inicial"

NAMESPACE=mlops-demo ./scripts/gitops-controller.sh /tmp/gitops-repo
```

En otra terminal, editá `/tmp/gitops-repo/manifests/model-server.yaml`,
commiteá el cambio, y mirá los logs del controlador reconciliando solo.
