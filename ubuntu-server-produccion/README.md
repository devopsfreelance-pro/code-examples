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

## Pasos para correrlo

Desde este directorio (`ubuntu-server-produccion/`):

```bash
# 1. Construir y levantar el contenedor.
#    El Dockerfile genera un par de claves de demo DENTRO de la imagen
#    (no hace falta material externo para que el build funcione).
docker compose up --build -d

# 2. Extraer la clave privada de demo generada en el contenedor
docker compose cp ubuntu-hardened:/home/deploy/.ssh/id_demo ./id_demo
chmod 600 id_demo

# 3. Conectarse por SSH usando la configuración endurecida (puerto 2222)
ssh -i id_demo -p 2222 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null deploy@localhost "echo conexion OK"

# 4. Correr el script de auditoría de hardening dentro del contenedor
docker compose exec ubuntu-hardened bash /scripts/audit-hardening.sh
```

## Salida esperada

Paso 3 (conexión SSH con clave, sin password):

```
conexion OK
```

Paso 4 (auditoría de hardening):

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
docker compose down -v --remove-orphans
rm -f id_demo
```

## Notas

- `id_demo` (la clave privada) se extrae del contenedor en el paso 2 y no se
  versiona (es material de clave, no forma parte del ejemplo en sí). La
  clave pública correspondiente (`authorized_keys`) se genera y queda solo
  dentro de la imagen.
- El usuario `deploy` es el mismo nombre usado en `AllowUsers deploy` del
  post; solo él puede autenticarse, y únicamente con clave pública.
