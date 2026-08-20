# Networking Linux - Mini laboratorio de network namespaces e iptables/nftables

Post: [Networking Linux: Guía Definitiva para DevOps en 2025](https://www.devopsfreelance.pro/blog/posts/networking-linux/)

## Qué demuestra este ejemplo

Un contenedor Ubuntu con `iproute2`, `iptables` y `nftables`, y dos
scripts que reproducen a mano los dos conceptos centrales del post:

- `netns-demo.sh` - crea un network namespace nuevo, lo conecta al
  namespace por defecto con un par `veth`, configura IPs a ambos lados
  y verifica conectividad con `ping` en las dos direcciones. Es
  exactamente lo que hace Docker cada vez que levanta un contenedor con
  red bridge, y lo que implementan los CNI de Kubernetes por debajo
  (sección "Creación de Network Namespaces" del post).
- `iptables-vs-nftables.sh` - carga una política de firewall (SSH
  permitido, resto bloqueado) primero con `iptables` en el orden
  correcto y en el orden incorrecto (para mostrar por qué el orden de
  las reglas importa), y después la misma política con `nftables`
  (sección "iptables vs nftables" del post).
- `cleanup.sh` - elimina el namespace y la interfaz `veth` creados por
  `netns-demo.sh`. Es idempotente: se puede correr aunque los recursos
  ya no existan.

## Requisitos

- Docker y Docker Compose
- El contenedor corre con `cap_add: NET_ADMIN, NET_RAW, SYS_ADMIN` y
  `security_opt: seccomp:unconfined, apparmor:unconfined`, necesarios
  para que `ip netns add` pueda montar `/run/netns` dentro del
  contenedor. No requiere `--privileged`.

## Cómo correrlo

```bash
cd networking-linux

# 1. Construir y levantar el contenedor
docker compose up -d --build

# 2. Namespaces + veth: crear, configurar y verificar conectividad
docker compose exec netns-lab ./netns-demo.sh

# 3. Limpiar el namespace y la interfaz veth antes del siguiente demo
docker compose exec netns-lab ./cleanup.sh

# 4. iptables (orden correcto vs incorrecto) y su equivalente en nftables
docker compose exec netns-lab ./iptables-vs-nftables.sh

# 5. Apagar y borrar todo (contenedor + imagen)
docker compose down --rmi local
```

## Salida esperada

### `netns-demo.sh`

```
== 1. Crear el namespace ==
== 2. Crear el par veth (dos interfaces virtuales unidas entre si) ==
== 3. Mover un extremo del par al namespace ==
== 4. Configurar IP y levantar el extremo dentro del namespace ==
== 5. Configurar IP y levantar el extremo en el host (namespace por defecto) ==

== 6. Verificar conectividad en ambas direcciones ==
--- host -> namespace ---
PING 10.0.0.1 (10.0.0.1) 56(84) bytes of data.
64 bytes from 10.0.0.1: icmp_seq=1 ttl=64 time=0.039 ms
...
--- 10.0.0.1 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2074ms

--- namespace -> host ---
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
...
3 packets transmitted, 3 received, 0% packet loss, time 2046ms

== 7. Interfaces y namespaces resultantes ==
--- namespaces ---
mi_namespace (id: 1)
--- interfaz en el host ---
veth0@if3        UP             10.0.0.2/24 ...
--- interfaz dentro del namespace ---
veth1@if4        UP             10.0.0.1/24 ...

Listo. Corre ./cleanup.sh para eliminar el namespace y el par veth.
```

### `iptables-vs-nftables.sh`

```
-- Politica CORRECTA: primero ACCEPT de SSH, despues DROP general --
Chain INPUT (policy ACCEPT)
num  target     prot opt source               destination
1    ACCEPT     6    --  0.0.0.0/0            0.0.0.0/0            tcp dpt:22
2    DROP       0    --  0.0.0.0/0            0.0.0.0/0

-- Comprobacion: el trafico SSH (puerto 22) matchea la regla 1 (ACCEPT) --
OK: la regla ACCEPT de SSH esta activa

-- Politica INCORRECTA (la que menciona el post): DROP antes del ACCEPT --
Chain INPUT (policy ACCEPT)
num  target     prot opt source               destination
1    DROP       0    --  0.0.0.0/0            0.0.0.0/0
2    ACCEPT     6    --  0.0.0.0/0            0.0.0.0/0            tcp dpt:22

Tabla nftables creada (se omiten otras tablas del sistema, p.ej. las de Docker):
table inet filter {
	chain input {
		type filter hook input priority filter; policy drop;
		ct state established,related accept
		tcp dport 22 accept
	}
}

Listo. Ambos bloques quedaron limpios (INPUT de iptables vaciada, tabla nftables eliminada).
```

## Notas

- Todo corre dentro del contenedor: el namespace `mi_namespace` y las
  reglas de `iptables`/`nftables` no tocan la red del host.
- `nft list ruleset` mostraría también las tablas NAT internas que
  Docker gestiona para la resolución de DNS del contenedor; por eso el
  script usa `nft list table inet filter` para mostrar solo la tabla
  creada por el demo.
