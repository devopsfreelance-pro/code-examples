# Seguridad en infraestructura blockchain: RPC expuesto vs restringido

Post relacionado: [Seguridad en infraestructura blockchain](https://www.devopsfreelance.pro/blog/posts/seguridad-infraestructura-blockchain/)

## Que demuestra este ejemplo

El post explica que el error mas comun en un nodo blockchain en produccion
es exponer el puerto RPC (8545) a Internet en vez de restringirlo a
localhost o a una red interna. Este mini-laboratorio reproduce ese
escenario con un mock de servidor JSON-RPC (no es un nodo Ethereum real,
no requiere sincronizar ninguna cadena) para que se pueda ver y ejecutar
en minutos:

- Dos contenedores identicos, uno con el RPC publicado en `0.0.0.0`
  (accesible desde cualquier interfaz del host) y otro publicado solo en
  `127.0.0.1` (equivalente a `--http.addr 127.0.0.1` en geth).
- Un script (`attack_demo.py`) que ataca el RPC expuesto: fingerprinting
  sin autenticacion, intento de enumerar cuentas y una consulta pesada
  tipo `eth_getLogs` (el vector de DoS que menciona el post).
- Un script (`generate-jwt.sh`) que genera el secreto JWT del engine API
  con la misma entropia y permisos (`chmod 600`) que recomienda el post.
- El `docker-compose.yml` fija la imagen local por tag para desarrollo,
  pero el comentario y el `Dockerfile` muestran donde iria el pinning por
  digest en un registry real (practica de supply chain del post).

No hay llaves, fondos ni datos reales en ningun lado: todo es un mock
pensado para ilustrar el concepto, no un cliente Ethereum.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- Python 3 en el host (para correr `attack_demo.py` fuera del contenedor)
- `openssl` (para `generate-jwt.sh`, viene preinstalado en la mayoria de
  las distros Linux/macOS)

## Pasos para correrlo

### 1. Levantar los dos nodos mock

```bash
cd seguridad-infraestructura-blockchain
docker compose up --build -d
```

Verifica que ambos contenedores esten corriendo:

```bash
docker compose ps
```

Salida esperada (dos servicios `Up`):

```
NAME            IMAGE            COMMAND                  STATUS
node-inseguro   mock-rpc:local   "python3 mock_rpc_s…"    Up
node-seguro     mock-rpc:local   "python3 mock_rpc_s…"    Up
```

### 2. Confirmar donde escucha cada uno

```bash
ss -tlnp | grep -E '8545|8546'
```

Salida esperada (nota la diferencia en la direccion de bind):

```
LISTEN 0  4096  0.0.0.0:8545   0.0.0.0:*
LISTEN 0  4096  127.0.0.1:8546 0.0.0.0:*
```

`0.0.0.0:8545` significa que, si no hay firewall delante, ese puerto es
alcanzable desde cualquier red a la que el host este conectado.
`127.0.0.1:8546` solo acepta conexiones que se originan en la misma
maquina.

### 3. Atacar el RPC expuesto

```bash
python3 attack_demo.py http://localhost:8545
```

Salida esperada (resumida):

```
[1] Fingerprinting sin autenticacion contra http://localhost:8545
    Respuesta: MockGeth/v0.0.0-demo/linux-amd64/python3
[2] Intentando enumerar cuentas (eth_accounts)
    Cuentas expuestas: ['0xDEMO0000000000000000000000000000000001']
    RIESGO: el nodo respondio con cuentas. En un nodo real esto habilita firmar transacciones.
[3] Consulta pesada eth_getLogs (vector de DoS)
    Tiempo total de la llamada: 0.3xxs (server reporto 0.2xxs de trabajo)
    En un nodo real, repetir esto en paralelo desde muchos scanners degrada el servicio.
```

### 4. Repetir contra el RPC restringido

```bash
python3 attack_demo.py http://localhost:8546
```

Desde `localhost` esto tambien responde (porque el script corre en el
mismo host), lo cual es correcto: el punto no es que `127.0.0.1` bloquee
al dueño de la maquina, sino que bloquea a cualquiera que no este en ella.
Para verlo de forma mas directa, repite el paso 2: `8546` nunca aparece
bindeado a `0.0.0.0`, asi que un firewall perimetral o un atacante en otra
red jamas llega a ese puerto, mientras que a `8545` si podria llegar si no
hay reglas de firewall delante.

### 5. Generar el secreto JWT del engine API

```bash
./generate-jwt.sh ./secrets
cat ./secrets/jwt.hex | wc -c   # 65 = 64 hex chars + salto de linea
ls -l ./secrets/jwt.hex         # debe mostrar permisos -rw------- (600)
```

### 6. Limpieza

```bash
docker compose down
rm -rf ./secrets
```

## Nota sobre el pinning de imagenes por digest

`docker-compose.yml` usa `image: mock-rpc:local` (build local, sin
digest) porque este ejemplo no publica a un registry. En un despliegue
real, tal como describe el post, la imagen se referencia por digest
inmutable una vez verificada:

```yaml
image: mock-rpc@sha256:<digest-verificado-del-release>
```

Sustituye `<digest-verificado-del-release>` por el digest real que
obtengas de `docker inspect --format='{{index .RepoDigests 0}}' mock-rpc:local`
despues de construir y verificar la imagen; no hay un digest fijo que
poner aqui porque depende de cada build.
