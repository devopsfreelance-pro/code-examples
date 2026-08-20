#!/bin/bash
# Demo de filtrado de paquetes con iptables, tal como se describe en el post
# "Configuracion de Firewalls y SELinux". Corre dentro del contenedor
# firewall-selinux-lab (necesita las capabilities NET_ADMIN/NET_RAW).
set -euo pipefail

log() { echo; echo "== $* =="; }

log "1. Arrancando un servidor HTTP local (httpd) para tener algo que proteger"
mkdir -p /var/www/html
echo "<h1>demo</h1>" > /var/www/html/index.html
echo "ServerName localhost" > /etc/httpd/conf.d/servername.conf
httpd -k start
sleep 1
curl -sS -o /dev/null -w "curl localhost:80 -> HTTP %{http_code}\n" http://127.0.0.1:80/ \
    || echo "curl localhost:80 -> FALLO (no deberia pasar todavia)"

log "2. Reglas base: permitir SSH solo desde una IP y trafico establecido/relacionado"
iptables -A INPUT -p tcp -s 192.168.1.100 --dport 22 -j ACCEPT
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -L INPUT -n -v --line-numbers

log "3. ANTES: puerto 80 abierto, la peticion HTTP entra sin problema"
curl -sS -o /dev/null -w "curl localhost:80 -> HTTP %{http_code}\n" http://127.0.0.1:80/

log "4. Bloqueando el puerto 80 con una regla DROP (como el ejemplo de bloqueo de red del post)"
iptables -A INPUT -p tcp --dport 80 -j DROP

log "5. DESPUES: la misma peticion ahora se queda sin respuesta (paquete descartado)"
if curl -sS -m 3 -o /dev/null -w "curl localhost:80 -> HTTP %{http_code}\n" http://127.0.0.1:80/; then
    echo "ADVERTENCIA: la peticion paso, revisar la regla"
else
    echo "curl localhost:80 -> timeout / conexion rechazada (regla DROP funcionando)"
fi

log "6. Quitando la regla DROP y confirmando que el trafico vuelve a pasar"
iptables -D INPUT -p tcp --dport 80 -j DROP
curl -sS -o /dev/null -w "curl localhost:80 -> HTTP %{http_code}\n" http://127.0.0.1:80/

log "7. Politica por defecto de la cadena INPUT (referencia, no se aplica para no cortar el propio contenedor)"
echo "Comando real en un servidor: iptables -P INPUT DROP"

log "8. Listado final de reglas activas"
iptables -L -n -v --line-numbers

httpd -k stop
echo
echo "Demo de firewall terminada."
