# Despliegue de infraestructura de staking: remote signer + proteccion contra slashing

Post original: [Guia Completa de Despliegue de staking infrastructure](https://www.devopsfreelance.pro/blog/posts/despliegue-staking-infrastructure/)

## Que demuestra este ejemplo

El post explica que en staking de Ethereum la pieza mas critica no es el
hardware sino la gestion de claves: la clave de validador nunca debe firmar
en dos maquinas a la vez porque eso provoca slashing (perdida de fondos).
La solucion que propone el post es un **remote signer** (Web3Signer) con una
base de datos de proteccion contra slashing (EIP-3076) delante del validador.

Este ejemplo levanta esa arquitectura completa y funcional en local:

1. **Postgres** con el esquema de proteccion contra slashing que usa
   Web3Signer en produccion (los mismos scripts SQL que trae la imagen
   oficial, copiados en `migrations/`).
2. Un job de **migracion** (Flyway) que aplica ese esquema antes de arrancar
   el signer.
3. **Web3Signer** (imagen oficial de ConsenSys) escuchando solo en
   `127.0.0.1:9000`, igual que en el `docker-compose.yml` del post, con
   `--slashing-protection-enabled=true` apuntando a esa base.
4. Las mismas **reglas de alerta de Prometheus** del post
   (`alerts/validator-alerts.yml`: atestacion perdida, balance decreciendo,
   propuesta perdida, slashing detectado), mas un script que las valida con
   `promtool` sin instalar Prometheus localmente.

No incluye claves de validador reales (generarlas requiere el deposito de
32 ETH y herramientas como `eth2-deposit-cli`, fuera del alcance de un
ejemplo local). Lo que se verifica es que el signer arranca, se conecta a
la base de proteccion contra slashing y responde en su API HTTP con cero
claves cargadas, listo para que en `keys/` se agreguen archivos de
configuracion YAML apuntando a keystores reales (formato documentado en
https://docs.web3signer.consensys.io/how-to/use-key-files).

## Requisitos

- Docker y Docker Compose (plugin `docker compose`).
- Puerto `9000` libre en `localhost`.
- Sin costos ni cuentas externas: todas las imagenes son publicas
  (`postgres`, `flyway/flyway`, `consensys/web3signer`, `prom/prometheus`).

## Pasos para correrlo

```bash
cd despliegue-staking-infrastructure

# 1. Levantar postgres, aplicar el esquema de slashing protection
#    y arrancar Web3Signer
docker compose up -d

# 2. Confirmar que los tres servicios terminaron su trabajo
docker compose ps
```

Salida esperada de `docker compose ps` (la migracion aparece "Exited (0)"
porque es un job que corre una vez y termina):

```
NAME                          STATUS
staking-slashing-db           Up (healthy)
staking-slashing-db-migrate   Exited (0)
staking-web3signer            Up
```

```bash
# 3. Verificar que Web3Signer esta vivo
curl -s http://localhost:9000/upcheck
# -> OK

# 4. Listar las claves cargadas (vacio: no hay keystores en keys/)
curl -s http://localhost:9000/api/v1/eth2/publicKeys
# -> []

# 5. Ver las tablas de proteccion contra slashing que Web3Signer
#    usa para rechazar doble firma (signed_blocks, signed_attestations,
#    low_watermarks, validators)
docker exec staking-slashing-db psql -U web3signer -d web3signer -c '\dt'

# 6. Validar la sintaxis y estructura de las reglas de alerta de
#    Prometheus del post, con promtool via Docker (no requiere
#    instalar Prometheus)
./check-alerts.sh
# -> Checking /alerts/validator-alerts.yml
#    SUCCESS: 4 rules found
```

Para limpiar todo (borra tambien el volumen de Postgres):

```bash
docker compose down -v
```

## Estructura

```
despliegue-staking-infrastructure/
├── docker-compose.yml       # postgres + migracion + web3signer
├── migrations/               # esquema SQL de proteccion contra slashing
│                              # (los mismos 12 scripts que trae la imagen
│                              #  oficial de Web3Signer en
│                              #  /opt/web3signer/migrations/postgresql)
├── keys/                     # directorio vacio: aqui van los YAML de
│                              # configuracion de claves (--key-store-path)
├── alerts/
│   └── validator-alerts.yml  # reglas de alerta del post (Prometheus)
├── check-alerts.sh           # valida alerts/ con promtool via Docker
└── README.md
```

## Notas

- `POSTGRES_PASSWORD=web3signer_demo` y las credenciales del
  `docker-compose.yml` son valores de demo para correr en local. En
  produccion van en un secret manager (AWS Secrets Manager, K8s Secret),
  nunca en texto plano en el compose.
- `--http-host-allowlist=*` se usa aqui solo porque el cliente (`curl`)
  corre en el host y no en la red del contenedor. En produccion se limita
  a los hosts que efectivamente consultan al signer.
- Este ejemplo cubre la pieza de "remote signer + slashing protection DB"
  del post. No reproduce MEV-boost, DVT (Obol/SSV) ni el patron de
  failover activo-pasivo, que requieren un cliente de consenso completo
  sincronizado con la red.
