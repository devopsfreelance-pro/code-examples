# Despliegue de nodos Ethereum con Kubernetes

Post: https://www.devopsfreelance.pro/blog/posts/despliegue-nodos-ethereum-con-kubernetes/

## Qué demuestra este ejemplo

Un patrón mínimo pero real de despliegue de un nodo Ethereum en Kubernetes,
con los elementos que menciona el post:

- **StatefulSet** con identidad estable y `volumeClaimTemplates` (almacenamiento
  persistente para los datos de la blockchain), en lugar de un `Deployment`.
- **Requests/limits de CPU y memoria** en el pod.
- **Readiness y liveness probes** sobre el puerto RPC del nodo.
- **NetworkPolicy** que aísla el nodo: solo expone el puerto RPC (8545) a pods
  con label `access=rpc-client` y el puerto P2P (30303) dentro del namespace.
- Namespace dedicado (`ethereum`).

Para que el ejemplo corra en minutos en una laptop, el nodo usa
`geth --dev` (chain efímera de un solo nodo, minado instantáneo de bloques,
sin sincronizar con la red real). Esto reemplaza la sincronización real de
mainnet, que tarda horas/días y no es viable para una demo local, pero
conserva exactamente el mismo patrón de despliegue en Kubernetes que usarías
con un nodo real (Geth, Erigon o Nethermind apuntando a mainnet/testnet).

## Requisitos

- [Docker](https://docs.docker.com/get-docker/)
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/) (Kubernetes in Docker)
- `kubectl`
- `curl`

No requiere cuentas ni claves de ningún proveedor cloud: todo corre local.

## Cómo correrlo

```bash
cd despliegue-nodos-ethereum-con-kubernetes
./deploy.sh
```

El script:

1. Crea un cluster kind llamado `ethereum-demo` (o reutiliza uno existente).
2. Aplica `namespace.yaml`, `statefulset.yaml`, `service.yaml` y `networkpolicy.yaml`.
3. Espera a que el StatefulSet esté `Ready`.
4. Hace `port-forward` del pod al puerto local 8545.
5. Consulta el número de bloque actual vía RPC (`eth_blockNumber`).

### Salida esperada

Al final del script deberías ver algo como:

```
==> Consultando eth_blockNumber via RPC...
{"jsonrpc":"2.0","id":1,"result":"0x3"}

==> Listo. Para borrar todo: kind delete cluster --name ethereum-demo
```

El valor de `result` es el número de bloque en hexadecimal (`0x3` = bloque 3);
con `--dev.period=2` el nodo minado un bloque nuevo cada ~2 segundos, así que
el número exacto varía según cuánto tardó en levantar el pod.

### Verificar manualmente

```bash
kubectl -n ethereum get pods,pvc,svc
kubectl -n ethereum logs statefulset/geth-node
kubectl -n ethereum describe networkpolicy geth-node-policy
```

### Limpiar

```bash
kind delete cluster --name ethereum-demo
```

## Archivos

- `namespace.yaml` — namespace `ethereum` dedicado.
- `statefulset.yaml` — nodo geth en modo `--dev`, con PVC, resources y probes.
- `service.yaml` — Service headless para el StatefulSet (RPC y P2P).
- `networkpolicy.yaml` — aísla el nodo, solo abre 8545 a clientes autorizados y 30303 al namespace.
- `deploy.sh` — crea el cluster kind, aplica los manifests y valida el RPC.

## Ir más allá (no cubierto por esta demo mínima)

- Reemplazar `--dev` por conexión a una red real (mainnet/Sepolia) usando un
  Helm chart de Geth/Erigon/Nethermind y un volumen de varios cientos de GB.
- Agregar un `HorizontalPodAutoscaler` (mencionado en el post) para escalar
  réplicas de nodos RPC de solo lectura detrás de un balanceador.
- Instalar `metrics-server` y Prometheus/Grafana para observabilidad, como
  recomienda la sección de buenas prácticas del post.
