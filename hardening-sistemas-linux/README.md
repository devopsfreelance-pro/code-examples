# Linux Hardening with Lynis Auditing - Mini Lab

Post: [Linux Hardening: Complete Server Security Guide](https://www.devopsfreelance.pro/blog/en/posts/linux-server-hardening-guide/)

## What this example demonstrates

An Ubuntu container with [Lynis](https://cisofy.com/lynis/) (the automated
auditing tool mentioned in the post alongside the CIS Benchmarks) and a
script (`harden.sh`) that applies a real subset of hardening controls at the
kernel, auditing, and account level:

- **Kernel/network (`sysctl-hardening.conf`)**: full ASLR, SYN cookies,
  disables IP forwarding and source routing, ignores ICMP redirects and
  broadcast pings, restricts `dmesg` and `ptrace`, disables core dumps for
  setuid binaries.
- **Auditing (`audit-hardening.rules`)**: CIS 4.1-style `auditd` rules that
  watch for changes to `/etc/passwd`, `/etc/shadow`, `/etc/sudoers`, and
  network/SSH configuration.
- **Accounts (`harden.sh`)**: password expiration policy
  (`PASS_MAX_DAYS`/`PASS_MIN_DAYS`), a stricter `umask`, restricted
  permissions on sensitive files, and a legal access banner.

Running `lynis audit system` **before** and **after** `harden.sh` shows the
"Hardening index" (a 0-100 score calculated by Lynis) go up with real data,
not simulated.

## Requirements

- Docker and Docker Compose

## How to run it

```bash
cd hardening-sistemas-linux

# 1. Build and start the container
docker compose up -d --build

# 2. Audit BEFORE hardening
docker compose exec hardening-lab lynis audit system --quick
docker compose exec hardening-lab grep hardening_index /var/log/lynis-report.dat

# 3. Apply hardening
docker compose exec hardening-lab harden.sh

# 4. Audit AFTER hardening
docker compose exec hardening-lab lynis audit system --quick
docker compose exec hardening-lab grep hardening_index /var/log/lynis-report.dat

# 5. Clean up
docker compose down --rmi local
```

## Expected output

Step 2 (before hardening), at the end of the Lynis report in
`/var/log/lynis.log`:

```
hardening_index=56
```

Step 3, `harden.sh` applying the controls:

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

Step 4 (after hardening):

```
hardening_index=59
```

The index goes up (56 → 59 in this lab's tests; the exact value may vary by
a couple of points depending on the base Ubuntu image version). To see the
full detail of what improved, compare the `suggestion[]=...` lines in
`/var/log/lynis-report.dat` before and after.

## Notes

- This is an educational lab, not a complete production hardening setup. A
  real server also needs a firewall (see the
  [`seguridad-servidores-linux`](../seguridad-servidores-linux/) example for
  `ufw`/`fail2ban`/SSH hardening), SELinux/AppArmor in enforcing mode, and
  automatic security updates.
- `auditd` **doesn't actually start as a daemon inside the container**
  (Docker doesn't expose the host kernel's audit netlink even if the
  `AUDIT_CONTROL`/`AUDIT_WRITE` capabilities are added); that's why the
  script only writes the rules to
  `/etc/audit/rules.d/hardening.rules`. On a real server (or with `systemd`
  available) those same rules get loaded when the service starts with
  `systemctl enable --now auditd`.
- The `sysctl-hardening.conf` parameters do get applied inside the container
  thanks to the `SYS_ADMIN` capability declared in `docker-compose.yml`; on a
  real host nothing special is needed, they're applied with
  `sysctl --system` or on reboot.
- `harden.sh` and the `.conf`/`.rules` files don't depend on anything
  Docker-specific: they can be copied as-is to a real Ubuntu/Debian server
  and run with `sudo`.

---

## 🇪🇸 Versión en español

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
