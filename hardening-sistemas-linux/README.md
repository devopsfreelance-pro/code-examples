# Hardening de Linux con auditoría Lynis - Mini laboratorio

Post: [Hardening Linux: Guía de Seguridad y Bastionado de Servidores](https://www.devopsfreelance.pro/blog/posts/hardening-sistemas-linux/)

## Qué demuestra este ejemplo

Un contenedor Ubuntu con [Lynis](https://cisofy.com/lynis/) (la herramienta
de auditoría automatizada que menciona el post junto a los CIS Benchmarks) y
un script (`harden.sh`) que aplica un subconjunto real de controles de
hardening a nivel de kernel, auditoría y cuentas:

- **Kernel/red (`sysctl-hardening.conf`)**: ASLR completo, SYN cookies,
  deshabilita IP forwarding y source routing, ignora ICMP redirects y
  broadcast pings, restringe `dmesg` y `ptrace`, desactiva core dumps de
  binarios setuid.
- **Auditoría (`audit-hardening.rules`)**: reglas de `auditd` estilo CIS 4.1
  que vigilan cambios en `/etc/passwd`, `/etc/shadow`, `/etc/sudoers`,
  configuración de red y de SSH.
- **Cuentas (`harden.sh`)**: política de expiración de contraseñas
  (`PASS_MAX_DAYS`/`PASS_MIN_DAYS`), `umask` más estricto, permisos
  restringidos en archivos sensibles y banner legal de acceso.

Corriendo `lynis audit system` **antes** y **después** de `harden.sh` se ve
el "Hardening index" (score 0-100 que calcula Lynis) subir con datos reales,
no simulados.

## Requisitos

- Docker y Docker Compose

## Cómo correrlo

```bash
cd hardening-sistemas-linux

# 1. Construir y levantar el contenedor
docker compose up -d --build

# 2. Auditoría ANTES del hardening
docker compose exec hardening-lab lynis audit system --quick
docker compose exec hardening-lab grep hardening_index /var/log/lynis-report.dat

# 3. Aplicar hardening
docker compose exec hardening-lab harden.sh

# 4. Auditoría DESPUÉS del hardening
docker compose exec hardening-lab lynis audit system --quick
docker compose exec hardening-lab grep hardening_index /var/log/lynis-report.dat

# 5. Limpiar
docker compose down --rmi local
```

## Salida esperada

Paso 2 (antes del hardening), al final del reporte de Lynis en
`/var/log/lynis.log`:

```
hardening_index=56
```

Paso 3, `harden.sh` aplicando los controles:

```
== Aplicando hardening de kernel (sysctl) ==
  parametros de kernel aplicados
== Configurando reglas de auditd (registro de eventos criticos) ==
  reglas escritas en /etc/audit/rules.d/hardening.rules
== Restringiendo permisos de archivos sensibles ==
== Deshabilitando core dumps de binarios setuid ==
== Politica de contrasenas y umask en /etc/login.defs ==
== Banner legal en /etc/issue y /etc/issue.net ==
== Hardening aplicado ==
```

Paso 4 (después del hardening):

```
hardening_index=59
```

El índice sube (56 → 59 en las pruebas de este laboratorio; el valor exacto
puede variar un par de puntos según la versión de la imagen base de Ubuntu).
Para ver el detalle completo de qué mejoró, comparar las líneas
`suggestion[]=...` de `/var/log/lynis-report.dat` antes y después.

## Notas

- Este es un laboratorio educativo, no un hardening completo de producción.
  Un servidor real necesita además firewall (ver el ejemplo de
  [`seguridad-servidores-linux`](../seguridad-servidores-linux/) para
  `ufw`/`fail2ban`/hardening de SSH), SELinux/AppArmor en modo enforcing, y
  actualizaciones automáticas de seguridad.
- `auditd` **no llega a arrancar como daemon dentro del contenedor** (Docker
  no expone el netlink de auditoría del kernel del host aunque se agreguen
  las capabilities `AUDIT_CONTROL`/`AUDIT_WRITE`); por eso el script solo
  escribe las reglas en `/etc/audit/rules.d/hardening.rules`. En un servidor
  real (o con `systemd` disponible) esas mismas reglas se cargan al iniciar
  el servicio con `systemctl enable --now auditd`.
- Los parámetros de `sysctl-hardening.conf` sí se aplican dentro del
  contenedor gracias a la capability `SYS_ADMIN` declarada en
  `docker-compose.yml`; en un host real no hace falta nada especial, se
  aplican con `sysctl --system` o al reiniciar.
- `harden.sh` y los archivos `.conf`/`.rules` no dependen de nada específico
  de Docker: se pueden copiar tal cual a un servidor Ubuntu/Debian real y
  correr con `sudo`.
