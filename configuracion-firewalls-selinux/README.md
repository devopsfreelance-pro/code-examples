# Configuracion de firewalls y SELinux - Mini laboratorio

Post: [Configuracion de Firewalls y SELinux: Guia Completa 2026](https://www.devopsfreelance.pro/blog/posts/configuracion-firewalls-selinux/)

## Que demuestra este ejemplo

Un contenedor basado en Rocky Linux 9 (misma familia RHEL que usa el post
para los ejemplos de `firewalld`/SELinux) con dos scripts que reproducen los
comandos del articulo:

- **`scripts/firewall-demo.sh`**: arranca un `httpd` local y prueba con
  `curl` que responde. Despues aplica las mismas reglas de `iptables` del
  post (permitir SSH solo desde una IP, aceptar trafico
  `ESTABLISHED,RELATED`, bloquear un puerto con `DROP`) y vuelve a probar
  con `curl` para mostrar, con datos reales y no simulados, como la
  peticion pasa **antes** de la regla `DROP` y se queda sin respuesta
  **despues**. Al final quita la regla y confirma que el trafico vuelve.
- **`scripts/selinux-demo.sh`**: corre los comandos de SELinux del post
  (`getenforce`, `sestatus`, `ls -Z`, `ps -Z`, `getsebool`). Ver la nota
  importante mas abajo sobre las limitaciones de SELinux dentro de Docker.

## Requisitos

- Docker y Docker Compose

## Como correrlo

```bash
cd configuracion-firewalls-selinux

# 1. Construir y levantar el contenedor
docker compose up -d --build

# 2. Demo de firewall (iptables): antes/despues de bloquear el puerto 80
docker compose exec firewall-selinux-lab scripts/firewall-demo.sh

# 3. Demo de SELinux: contextos, procesos y booleanos
docker compose exec firewall-selinux-lab scripts/selinux-demo.sh

# 4. Limpiar
docker compose down --rmi local
```

## Salida esperada

Paso 2 (`firewall-demo.sh`), lo relevante:

```
== 3. ANTES: puerto 80 abierto, la peticion HTTP entra sin problema ==
curl localhost:80 -> HTTP 200

== 4. Bloqueando el puerto 80 con una regla DROP (como el ejemplo de bloqueo de red del post) ==

== 5. DESPUES: la misma peticion ahora se queda sin respuesta (paquete descartado) ==
curl localhost:80 -> timeout / conexion rechazada (regla DROP funcionando)

== 6. Quitando la regla DROP y confirmando que el trafico vuelve a pasar ==
curl localhost:80 -> HTTP 200
```

Paso 3 (`selinux-demo.sh`), en un host/contenedor sin kernel SELinux (el
caso mas comun con Docker en Ubuntu/macOS/WSL):

```
== 1. Estado de SELinux en este kernel ==
/sys/fs/selinux no existe: el kernel de este host/contenedor no
tiene SELinux compilado o habilitado. getenforce/sestatus abajo
muestran el estado real, que sera 'disabled':
Disabled
```

## Nota importante sobre SELinux y Docker

SELinux es una caracteristica del **kernel**, no de un paquete que se
instala y ya funciona. Un contenedor Docker comparte el kernel del host, asi
que si el host (Ubuntu, macOS con Docker Desktop, WSL2, etc.) no tiene
SELinux compilado, `getenforce` va a devolver `Disabled` dentro del
contenedor sin importar que `policycoreutils` este instalado. Esto no es un
error del script: es la razon por la que en produccion SELinux se configura
en el propio host RHEL/Rocky/CentOS/Fedora, no dentro de un contenedor.

`scripts/selinux-demo.sh` detecta esta situacion, la explica, y al final
imprime la lista completa de comandos del post como referencia para correr
en un host o VM con SELinux real (por ejemplo `vagrant` con una box
`rockylinux/9` o un EC2 con AMI RHEL/Rocky).

La parte de `iptables` (`scripts/firewall-demo.sh`) si funciona de punta a
punta dentro de Docker porque el filtrado de paquetes en la cadena `INPUT`
se aplica tambien al trafico por `lo` (loopback), gracias a las capabilities
`NET_ADMIN`/`NET_RAW` declaradas en `docker-compose.yml`.

## Notas adicionales

- `iptables -P INPUT DROP` (politica por defecto del post) no se ejecuta en
  el script para no cortar el propio acceso `docker compose exec` al
  contenedor; queda documentado como comentario en el script.
- Los comandos de `firewalld` del post (`firewall-cmd --add-service=http`,
  etc.) requieren el daemon `firewalld` corriendo con `systemd`/D-Bus, que
  no arranca de forma confiable dentro de un contenedor sin `systemd` como
  PID 1. Por eso este laboratorio usa `iptables` directamente para la parte
  de firewall: son las mismas reglas de bajo nivel que `firewalld` termina
  aplicando via `nftables`/`iptables` como backend.
