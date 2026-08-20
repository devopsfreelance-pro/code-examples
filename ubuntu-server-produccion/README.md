# Ubuntu Server para producción - demo de hardening

Post: https://www.devopsfreelance.pro/blog/posts/ubuntu-server-produccion/

## Qué demuestra este ejemplo

El post explica cómo endurecer un Ubuntu Server para producción: SSH sin
contraseña ni root, actualizaciones desatendidas limitadas a parches de
seguridad, y auditoría de archivos sensibles con `auditd`.

Este ejemplo levanta un contenedor Ubuntu 22.04 con esas tres medidas
aplicadas EXACTAMENTE con la configuración del post
(`config/sshd_config`, `config/50unattended-upgrades`, `config/audit.rules`),
y agrega un script (`scripts/audit-hardening.sh`) que audita el servidor y
confirma que el hardening quedó bien aplicado, con un score final.

No usa `ufw` ni arranca `auditd` como daemon real porque un contenedor sin
privilegios no tiene el subsistema de auditoría del kernel ni `iptables`
disponibles; el foco del ejemplo es SSH endurecido + actualizaciones
desatendidas + reglas de auditoría versionadas, que es la parte
reproducible en cualquier máquina.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- `ssh-keygen` (viene con OpenSSH client, ya instalado en Linux/macOS)

## Pasos para correrlo

Desde este directorio (`ubuntu-server-produccion/`):

```bash
# 1. Generar un par de claves SSH solo para esta demo
ssh-keygen -t ed25519 -f id_demo -N ""

# 2. Copiar la clave pública para que el Dockerfile la incluya en el usuario deploy
cp id_demo.pub authorized_keys

# 3. Construir y levantar el contenedor
docker compose up --build -d

# 4. Conectarse por SSH usando la configuración endurecida (puerto 2222)
ssh -i id_demo -p 2222 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null deploy@localhost "echo conexion OK"

# 5. Correr el script de auditoría de hardening dentro del contenedor
docker compose exec ubuntu-hardened bash /scripts/audit-hardening.sh
```

## Salida esperada

Paso 4 (conexión SSH con clave, sin password):

```
conexion OK
```

Paso 5 (auditoría de hardening):

```
== Hardening de SSH (/etc/ssh/sshd_config) ==
[OK]   Puerto SSH distinto de 22
[OK]   Login root deshabilitado
[OK]   Autenticación por password deshabilitada
[OK]   Autenticación por clave pública habilitada
[OK]   Lista blanca de usuarios (AllowUsers) presente
[OK]   MaxAuthTries restringido (<=3)

== Actualizaciones desatendidas (/etc/apt/apt.conf.d/50unattended-upgrades) ==
[OK]   Solo se permiten actualizaciones de seguridad
[OK]   Reinicio automático deshabilitado

== Auditoría de archivos sensibles (/etc/audit/rules.d/audit.rules) ==
[OK]   Vigila /etc/passwd
[OK]   Vigila /etc/shadow
[OK]   Vigila /etc/sudoers

Resultado: 11/11 checks OK (score: 100/100)
```

Si intentás conectar con password (`ssh -p 2222 deploy@localhost` sin `-i`)
la conexión debe ser rechazada, porque `PasswordAuthentication no` está
aplicado igual que en el post.

## Limpieza

```bash
docker compose down
rm -f id_demo id_demo.pub authorized_keys
```

## Notas

- `authorized_keys`, `id_demo` e `id_demo.pub` se generan localmente en el
  paso 1-2 y no se versionan (son material de clave, no forman parte del
  ejemplo en sí).
- El usuario `deploy` es el mismo nombre usado en `AllowUsers deploy` del
  post; solo él puede autenticarse, y únicamente con clave pública.
