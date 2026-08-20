# Networking Avanzado en Linux - Mini laboratorio de policy-based routing y tc/QoS

Post: [Networking Avanzado en Linux: Guía Completa para Profesionales](https://www.devopsfreelance.pro/blog/posts/networking-avanzado-linux/)

## Qué demuestra este ejemplo

Un contenedor Ubuntu con `iproute2` y dos scripts que reproducen, con
verificación real (no solo comandos copiados), las dos secciones más
avanzadas del post:

- `policy-routing-lab.sh` - crea dos interfaces `dummy` (simulan dos
  uplinks / ISPs), una tabla de rutas independiente para cada una, y
  reglas `ip rule` que seleccionan la tabla según la dirección de
  origen del paquete. Verifica con `ip route get ... from <origen>`
  que el kernel realmente elige la interfaz correcta según el origen,
  tal como describe la sección "Tablas de Enrutamiento Múltiples" y
  "Policy-Based Routing" del post.
- `tc-bandwidth-shaping.sh` - crea un par `veth` entre el host y un
  network namespace, transfiere un archivo de 5MB con `nc` y mide el
  throughput real (baseline sin límite), después aplica un qdisc `htb`
  que limita el egreso a 1mbit y repite la transferencia para
  comprobar que el ancho de banda medido cae y se acerca al límite
  configurado (sección "Traffic Control (tc) y QoS" del post).
- `cleanup.sh` - elimina namespace, interfaces `dummy`/`veth`, tablas
  de rutas, reglas y el qdisc creados por los dos scripts anteriores.
  Es idempotente: se puede correr aunque los recursos ya no existan.

## Requisitos

- Docker y Docker Compose
- El contenedor corre con `cap_add: NET_ADMIN, NET_RAW, SYS_ADMIN` y
  `security_opt: seccomp:unconfined, apparmor:unconfined`, necesarios
  para crear namespaces, interfaces `dummy`/`veth`, tablas de rutas y
  qdiscs dentro del contenedor. No requiere `--privileged`.

## Cómo correrlo

```bash
cd networking-avanzado-linux

# 1. Construir y levantar el contenedor
docker compose up -d --build

# 2. Policy-based routing: tablas múltiples + verificación con ip route get
docker compose exec netadv-lab ./policy-routing-lab.sh

# 3. Limpiar antes del siguiente demo (namespaces/interfaces no se pisan)
docker compose exec netadv-lab ./cleanup.sh

# 4. Traffic control: baseline vs tráfico limitado con tc htb
docker compose exec netadv-lab ./tc-bandwidth-shaping.sh

# 5. Limpiar de nuevo (opcional, el contenedor se descarta en el paso 6)
docker compose exec netadv-lab ./cleanup.sh

# 6. Apagar y borrar todo (contenedor + imagen)
docker compose down --rmi local
```

## Salida esperada

### `policy-routing-lab.sh` (paso 2)

En el paso 5 del script (`ip route get`), la salida debe mostrar una
interfaz distinta según el origen del paquete:

```
--- paquete con origen en 10.10.1.0/24 hacia 8.8.8.8 ---
8.8.8.8 from 10.10.1.1 dev dummy1 table 100
    cache

--- paquete con origen en 10.10.2.0/24 hacia 8.8.8.8 ---
8.8.8.8 from 10.10.2.1 dev dummy2 table 200
    cache
```

Esto confirma que el kernel eligió `dummy1`/tabla 100 para el origen
de la red A y `dummy2`/tabla 200 para el origen de la red B: el
policy-based routing funciona.

### `tc-bandwidth-shaping.sh` (paso 4)

La transferencia baseline (sin límite) corre a la velocidad real del
par `veth` (normalmente varios cientos de mbit/s o más, según el
host). Después de aplicar `tc qdisc add ... htb rate 1mbit`, la
segunda transferencia debe acercarse a 1 mbit/s:

```
== 3. Transferencia SIN shaping (baseline) ==
baseline: .01s -> 3389.40 mbit/s

== 5. Transferencia CON shaping (deberia acercarse a 1mbit) ==
shaped: 43.32s -> .92 mbit/s
```

Los números exactos varían según el hardware, pero la relación se
mantiene: la transferencia shaped debe ser drásticamente más lenta y
cercana a la tasa configurada en `tc`.

## Notas

- Este ejemplo no repite el laboratorio de `network namespaces` +
  `iptables`/`nftables` que ya existe en
  [`../networking-linux`](../networking-linux): se enfoca en los dos
  temas que el post de networking avanzado agrega sobre ese
  (enrutamiento basado en políticas con tablas múltiples y traffic
  shaping con `tc`).
- Temas del post que requieren hardware o kernel específico (bonding
  de NICs físicas, XDP/eBPF compilado con `clang`, afinidad NUMA de
  IRQs, Open vSwitch/SDN, Suricata) no se replican acá porque no son
  reproducibles de forma confiable en un contenedor genérico en
  minutos; el foco quedó en las dos técnicas que sí se pueden verificar
  end-to-end con herramientas estándar de `iproute2`.
