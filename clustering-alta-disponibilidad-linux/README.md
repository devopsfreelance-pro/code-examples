# Cluster HA activo-activo con HAProxy (mini demo)

Post relacionado: [Guía Definitiva de Clustering y Alta Disponibilidad en Linux](https://www.devopsfreelance.pro/blog/posts/clustering-alta-disponibilidad-linux/)

## Qué demuestra este ejemplo

El post describe clusters activo-activo balanceados con HAProxy y el proceso
de failover automático (detección de fallo, aislamiento del nodo caído,
redirección del tráfico). Este ejemplo reproduce esa idea central en Docker,
sin necesitar máquinas dedicadas ni una instalación completa de Pacemaker/Corosync:

- Dos nodos web (`web1`, `web2`) que representan los nodos del cluster.
- Un `haproxy` en frente, en modo `roundrobin`, con health check activo
  (`option httpchk`) que monitoriza ambos nodos cada 2 segundos.
- Un script (`test-failover.sh`) que apaga un nodo en caliente y muestra
  cómo HAProxy deja de enviarle tráfico automáticamente (failover) y cómo
  lo reincorpora al volver (failback), todo sin downtime del servicio.

No se implementa Pacemaker/Corosync/DRBD reales porque requieren múltiples
hosts con systemd, red multicast y fencing por hardware (IPMI), algo que no
se puede reproducir de forma fiel en unos pocos contenedores locales. Este
ejemplo se enfoca en el mecanismo de detección de fallos + balanceo +
failover automático, que es el concepto central y reproducible del post.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- `curl` (para probar el balanceo y el failover)

## Pasos para ejecutarlo

```bash
cd clustering-alta-disponibilidad-linux

# 1) Levantar el cluster (2 nodos web + HAProxy)
docker compose up -d

# 2) Ver que ambos nodos están "up" en HAProxy
curl -s http://localhost:8080/haproxy?stats | grep -o 'web[12]' | sort -u

# 3) Probar el balanceo activo-activo (alterna entre los dos nodos)
for i in $(seq 1 6); do curl -s http://localhost:8080 | grep -o "NODO [0-9]"; done

# 4) Correr la demo de failover automático
bash test-failover.sh

# 5) Apagar el cluster
docker compose down
```

## Salida esperada

En el paso 3, las respuestas alternan entre los dos nodos:

```
NODO 1
NODO 2
NODO 1
NODO 2
NODO 1
NODO 2
```

En `test-failover.sh`, al apagar `web1` el tráfico pasa a servirse
exclusivamente por `web2` sin errores ni caída del servicio:

```
== 1) Trafico normal (activo-activo, round robin) ==
NODO 1
NODO 2
NODO 1
NODO 2

== 2) Simulando caida del nodo web1 ==
[+] Stopping 1/1

== 3) Trafico durante el fallo (debe responder solo web2) ==
NODO 2
NODO 2
NODO 2
NODO 2
```

Es normal ver una única línea `(sin respuesta)` justo en el instante exacto
en que el nodo cae (la request llegó a web1 microsegundos antes de que
HAProxy lo marcara down); a partir de ahí todo el tráfico se sirve por
web2 sin más interrupciones. Esto es justamente el comportamiento de
detección de fallos + failover descrito en el post.

```

== 4) Recuperando el nodo web1 (failback) ==

== 5) Trafico tras la recuperacion (vuelve el balanceo entre ambos) ==
NODO 1
NODO 2
NODO 1
NODO 2

Prueba de failover completada.
```

## Archivos

- `docker-compose.yml` — define los dos nodos web y el balanceador HAProxy.
- `haproxy.cfg` — configuración de HAProxy: balanceo `roundrobin` + health check.
- `web1/index.html`, `web2/index.html` — contenido estático que identifica a cada nodo.
- `test-failover.sh` — script que simula la caída y recuperación de un nodo.

No hay secretos ni credenciales en este ejemplo.
