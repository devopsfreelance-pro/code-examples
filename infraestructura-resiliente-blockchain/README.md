# Infraestructura resiliente para blockchain - ejemplo ejecutable

Post relacionado: [Infraestructura resiliente para blockchain](https://www.devopsfreelance.pro/blog/posts/infraestructura-resiliente-blockchain/)

## Que demuestra este ejemplo

El post describe una infraestructura de nodos blockchain con redundancia,
balanceo de carga y tolerancia a fallos. Este ejemplo levanta una version
mini pero real de esa arquitectura en tu maquina:

- **3 nodos blockchain** (`node-a`, `node-b`, `node-c`): cada uno es un
  servicio HTTP que simula minar bloques (incrementa un contador) y expone
  `/health` para los healthchecks.
- **1 balanceador de carga** (nginx) que distribuye trafico entre los 3
  nodos con `least_conn` y saca de rotacion automaticamente al nodo que
  falla (`max_fails` / `fail_timeout`).
- **Un script de prueba de resiliencia** que manda requests en loop, mata
  uno de los nodos a mitad del test y comprueba que el balanceador siga
  respondiendo 200 usando los nodos restantes, tal como describe la seccion
  "Redundancia y replicación" y "Balanceo de carga dinámico" del post.

No implementa un protocolo de consenso real ni P2P entre nodos: el foco es
la capa de infraestructura (redundancia + balanceo + auto-recuperacion),
que es el tema central del post.

## Requisitos

- Docker y Docker Compose (plugin `docker compose`, version 2.x)
- `curl`
- `python3` (usado por el script de test para parsear el JSON de respuesta)

No se necesita cuenta ni credencial de ningun proveedor: todo corre local.

## Como correrlo

1. Entrar al directorio del ejemplo:

```bash
cd infraestructura-resiliente-blockchain
```

2. Levantar los 3 nodos y el balanceador:

```bash
docker compose up -d --build
```

3. Esperar unos segundos a que los healthchecks pasen y verificar que todo
   este arriba:

```bash
docker compose ps
```

Deberias ver `node-a`, `node-b`, `node-c` y `load-balancer` en estado
`running` (los nodos con `healthy` despues de ~5-10 segundos).

4. Probar el balanceador manualmente (cada request puede caer en un nodo
   distinto):

```bash
curl http://localhost:8080/
```

Salida esperada (el `node` y `block_height` varian):

```json
{"node":"node-b","block_height":3,"timestamp":"2026-08-20T18:00:00.123456+00:00"}
```

5. Correr el test de resiliencia (mata `node-a` a mitad de camino y lo
   vuelve a levantar al final):

```bash
chmod +x scripts/test-resilience.sh
./scripts/test-resilience.sh
```

Salida esperada (resumida):

```
== Test de resiliencia: infraestructura blockchain ==
Enviando 20 requests al balanceador (http://localhost:8080)...

request 1: OK (200) atendido por node-c
request 2: OK (200) atendido por node-a
...
>>> Simulando fallo: deteniendo node-a
request 8: OK (200) atendido por node-b
request 9: OK (200) atendido por node-c
...
>>> Restaurando node-a

RESULTADO: 20/20 requests exitosos pese a la caida de node-a.
```

6. Limpiar todo al terminar:

```bash
docker compose down
```

## Estructura

```
infraestructura-resiliente-blockchain/
├── docker-compose.yml       # orquesta 3 nodos + balanceador
├── app/
│   ├── node.py               # servidor Flask que simula un nodo blockchain
│   └── Dockerfile
├── nginx/
│   └── nginx.conf             # balanceo de carga con failover automatico
└── scripts/
    └── test-resilience.sh    # prueba de caida y recuperacion de un nodo
```
