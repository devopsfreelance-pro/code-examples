# Kubernetes para aplicaciones stateful

Ejemplo de código del post: [Guía Completa de Kubernetes para aplicaciones stateful](https://www.devopsfreelance.pro/blog/posts/kubernetes-aplicaciones-stateful/)

## Qué demuestra

El concepto central del post: las dos cosas que un `StatefulSet` le da a una
aplicación con estado y que un `Deployment` no da:

1. **Identidad de red estable**: los pods se llaman siempre `web-0`, `web-1`,
   `web-2` (no un hash aleatorio), y son direccionables individualmente vía
   `web-0.web-headless`, `web-1.web-headless`, etc. gracias al Headless
   Service.
2. **Almacenamiento persistente por pod**: cada réplica tiene su propio
   `PersistentVolumeClaim` creado a partir de `volumeClaimTemplates`. Si se
   borra el pod `web-0`, Kubernetes lo recrea con el **mismo nombre y el
   mismo PVC**, así que los datos escritos antes siguen ahí.

El script `demo.sh` prueba esto en la práctica: escribe un dato en `web-0`,
borra el pod, espera a que Kubernetes lo recree y verifica que el dato sigue
presente.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/)
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) (Kubernetes in Docker)
- [kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl)

No hace falta ninguna cuenta ni servicio pago: todo corre local en un cluster
kind de un solo nodo.

## Archivos

- `statefulset.yaml`: Headless Service + StatefulSet de 3 réplicas con
  `volumeClaimTemplates` (100Mi cada una, `storageClassName: standard`, la
  StorageClass por defecto que trae kind vía `local-path-provisioner`).
- `demo.sh`: automatiza todo el flujo de prueba descrito arriba.

## Pasos para correrlo

```bash
cd kubernetes-aplicaciones-stateful

# Da permisos de ejecución si hace falta
chmod +x demo.sh

# Corre la demo completa (crea el cluster kind si no existe)
./demo.sh
```

Al terminar, para limpiar todo:

```bash
kind delete cluster --name stateful-demo
```

### Para inspeccionar manualmente

```bash
# Ver que los nombres de pod son estables y no cambian al recrearse
kubectl get pods -l app=web -o wide

# Ver un PVC por pod, ligado 1 a 1
kubectl get pvc -l app=web

# Resolver la identidad de red estable de cada pod (desde dentro del cluster)
kubectl run -it --rm dns-test --image=busybox:1.36 --restart=Never -- \
  nslookup web-1.web-headless
```

## Salida esperada

Al correr `./demo.sh` vas a ver algo similar a esto (los timestamps y el
nombre del cluster van a variar):

```
==> 1. Creando cluster kind 'stateful-demo' (si no existe)...
...
==> 3. Esperando a que los 3 pods estén Ready...
statefulset rolling update complete 3 pods at revision web-xxxxxxxxxx...

==> Pods con nombre estable (no hash aleatorio como en un Deployment):
NAME    READY   STATUS    RESTARTS   AGE   IP           NODE
web-0   1/1     Running   0          20s   10.244.0.5   stateful-demo-control-plane
web-1   1/1     Running   0          15s   10.244.0.6   stateful-demo-control-plane
web-2   1/1     Running   0          10s   10.244.0.7   stateful-demo-control-plane

==> PVCs creados a partir de volumeClaimTemplates (uno por pod):
NAME          STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
data-web-0    Bound    pvc-...  100Mi      RWO            standard       20s
data-web-1    Bound    pvc-...  100Mi      RWO            standard       15s
data-web-2    Bound    pvc-...  100Mi      RWO            standard       10s

==> 4. Escribiendo un dato único en web-0...
dato-critico-1755600000

==> 5. Borrando el pod web-0 (Kubernetes lo va a recrear con el mismo nombre y el mismo PVC)...
pod "web-0" deleted

==> 6. Verificando que el dato sigue ahí después de recrear el pod...
    Contenido leído: dato-critico-1755600000

OK: el dato sobrevivió al borrado del pod. El PVC quedó ligado a web-0 (identidad estable + storage persistente).
```

## Notas

- Este ejemplo usa `nginx` en vez de una base de datos real (PostgreSQL,
  MongoDB, etc.) para que sea liviano y arranque en segundos. El post explica
  cómo aplicar el mismo patrón (`StatefulSet` + `Headless Service` +
  `volumeClaimTemplates`) a bases de datos productivas.
- No usar `PersistentVolumeReclaimPolicy: Delete` en el StorageClass de
  producción si querés que los datos sobrevivan también al borrado del
  `StatefulSet` completo (no solo al borrado de un pod individual).
