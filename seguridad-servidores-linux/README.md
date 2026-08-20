# Seguridad en servidores Linux - Mini laboratorio de hardening

Post: [Seguridad en servidores Linux: Guía esencial para DevOps](https://www.devopsfreelance.pro/blog/posts/seguridad-servidores-linux/)

## Qué demuestra este ejemplo

Un contenedor Ubuntu que simula un servidor **recién provisionado y sin
hardening** (root login por SSH habilitado, autenticación por password,
sin firewall, sin fail2ban, sin política de expiración de contraseñas) y
dos scripts que aplican los controles del post:

- `audit.sh` - mini auditoría estilo CIS Benchmark. Revisa 6 controles
  (SSH root login, SSH password auth, firewall `ufw` activo, `fail2ban`
  corriendo, expiración de contraseñas, archivos world-writable en
  `/etc`) e imprime `[OK]`/`[FAIL]` por cada uno. Termina con exit code
  `1` si hay fallas (pensado para usarse como gate en CI/CD).
- `hardening.sh` - corrige automáticamente los 6 controles anteriores
  (equivalente a los pasos "Configuración de firewall" y "Autenticación
  segura" del post).

Corriendo `audit.sh` antes y después de `hardening.sh` se ve el
antes/después de un hardening real.

## Requisitos

- Docker y Docker Compose

## Cómo correrlo

```bash
cd seguridad-servidores-linux

# 1. Construir y levantar el contenedor (necesita NET_ADMIN/NET_RAW
#    para que ufw pueda manipular reglas de firewall dentro del contenedor)
docker compose up -d --build

# 2. Auditoría ANTES del hardening (va a fallar varios controles)
docker compose exec hardening-lab audit.sh

# 3. Aplicar hardening
docker compose exec hardening-lab hardening.sh

# 4. Auditoría DESPUÉS del hardening (todos los controles en OK)
docker compose exec hardening-lab audit.sh

# 5. Limpiar
docker compose down --rmi local
```

## Salida esperada

Paso 2 (antes del hardening):

```
== Auditoria de hardening Linux ==

[FAIL] SSH: PermitRootLogin deshabilitado
[FAIL] SSH: PasswordAuthentication deshabilitado (solo claves)
[FAIL] Firewall (ufw) activo
[FAIL] fail2ban activo (proteccion contra fuerza bruta)
[FAIL] Politica de contraseñas: PASS_MAX_DAYS <= 90 (actual: 99999)
[OK]   Sin archivos world-writable en /etc

== Resumen: 1 OK / 5 FAIL ==
```

Paso 4 (después del hardening):

```
== Auditoria de hardening Linux ==

[OK]   SSH: PermitRootLogin deshabilitado
[OK]   SSH: PasswordAuthentication deshabilitado (solo claves)
[OK]   Firewall (ufw) activo
[OK]   fail2ban activo (proteccion contra fuerza bruta)
[OK]   Politica de contraseñas: PASS_MAX_DAYS <= 90 (actual: 90)
[OK]   Sin archivos world-writable en /etc

== Resumen: 6 OK / 0 FAIL ==
```

## Notas

- El contenedor usa una contraseña de root trivial (`root:root`) y SSH
  con password auth habilitado **a propósito**, para tener algo que
  hardenear. No es apto para producción ni para exponerlo a internet;
  es solo un laboratorio local.
- `ufw` necesita las capabilities `NET_ADMIN` y `NET_RAW` para poder
  escribir reglas de `iptables` dentro del contenedor; ya están
  declaradas en `docker-compose.yml`.
- Para adaptarlo a un servidor real, `audit.sh` y `hardening.sh` se
  pueden copiar tal cual (no dependen de nada específico de Docker) y
  correr con `sudo` sobre Ubuntu/Debian.
