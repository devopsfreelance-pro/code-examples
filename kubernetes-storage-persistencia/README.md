# Kubernetes Storage: persistencia de datos

Ejemplo de código del post: [Kubernetes Storage: Guía completa de persistencia de datos](https://www.devopsfreelance.pro/blog/posts/kubernetes-storage-persistencia/)

## Qué demuestra

El concepto central del post: la relación entre **StorageClass**,
**PersistentVolumeClaim (PVC)** y **PersistentVolume (PV)**, y por qué el
almacenamiento persistente vive **independientemente del pod** que lo usa:

1. **Aprovisionamiento dinámico**: se define una `StorageClass` propia
   (`fast-storage`) y, al crear un `PersistentVolumeClaim` contra ella, se
   crea automáticamente un `PersistentVolume` sin que nadie lo haya
   provisionado a mano. Con `volumeBindingMode: WaitForFirstConsumer` el PV
   recién se crea cuando hay un pod que efectivamente lo va a montar.
2. **Persistencia más allá del pod**: se escribe un dato en el volumen, se
   borra el pod y se recrea. El dato sigue ahí porque el PVC y el PV no
   dependen del ciclo de vida del pod.
3. **Ciclo de vida del PV según `reclaimPolicy`**: al borrar el PVC, con
   `reclaimPolicy: Delete` el PV pasa a `Released` y el provisioner lo
   elimina automáticamente (con `Retain` quedaría huérfano hasta limpiarlo
   a mano).

El script `demo.sh` ejecuta los tres pasos en orden y verifica cada uno.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/)
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) (Kubernetes in Docker)
- [kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl)

Todo corre local en un cluster kind de un solo nodo. No hace falta ninguna
cuenta ni servicio pago: se reutiliza el provisioner `rancher.io/local-path`
que trae kind por defecto (equivalente local a un CSI driver dinámico como
el de AWS EBS o Rook Ceph en un cluster real).

## Archivos

- `storageclass.yaml`: `StorageClass` `fast-storage` sobre el provisioner
  `rancher.io/local-path`, con `reclaimPolicy: Delete` y
  `volumeBindingMode: WaitForFirstConsumer`.
- `pvc.yaml`: `PersistentVolumeClaim` de 200Mi contra `fast-storage`.
- `pod.yaml`: pod `busybox` que monta el PVC en `/datos`.
- `demo.sh`: automatiza todo el flujo descrito arriba.

## Pasos para correrlo

```bash
cd kubernetes-storage-persistencia

# Da permisos de ejecución si hace falta
chmod +x demo.sh

# Corre la demo completa (crea el cluster kind si no existe)
./demo.sh
```

Al terminar, para borrar el cluster de prueba:

```bash
kind delete cluster --name storage-demo
```

## Salida esperada (resumida)

```
==> 1. Creando cluster kind 'storage-demo' (si no existe)...
...
==> 2. Aplicando StorageClass 'fast-storage'...
storageclass.storage.k8s.io/fast-storage created
NAME                 PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
fast-storage         rancher.io/local-path   Delete          WaitForFirstConsumer   false                  1s
standard (default)   rancher.io/local-path   Delete          WaitForFirstConsumer   false                  2m

==> 3. Creando PVC y Pod que lo consume...
    Esperando a que el pod este Ready...
pod/app-datos condition met

==> 4. PVC vinculado a un PV creado dinamicamente:
NAME            STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
datos-app-pvc   Bound    pvc-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx   200Mi      RWO            fast-storage   2s

    PV asociado: pvc-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM
pvc-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx   200Mi      RWO            Delete           Bound    default/datos-app-pvc

==> 5. Escribiendo un dato en el volumen...
dato-critico-1755600000

==> 6. Borrando el POD (el PVC y el PV quedan intactos)...
pod "app-datos" deleted
pod/app-datos created
pod/app-datos condition met

==> Verificando que el dato sigue ahi tras recrear el pod...
    Contenido leido: dato-critico-1755600000

OK: el dato sobrevivio al borrado del pod. El PV vive independiente del pod que lo consume.

==> 7. Borrando el PVC para ver el ciclo de vida del PV (reclaimPolicy: Delete)...
    El PV 'pvc-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx' ya fue eliminado por el garbage collector (reclaimPolicy: Delete).

==> Para limpiar todo:
    kind delete cluster --name storage-demo
```
