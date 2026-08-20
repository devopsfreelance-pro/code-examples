# Gestion de servicios con systemd - ejemplo ejecutable

Post: [Gestion de servicios con systemd: Guia completa para DevOps](https://www.devopsfreelance.pro/blog/posts/gestion-servicios-con-systemd/)

## Que demuestra

Un unit file de servicio (`webapp.service`) gestionando una aplicacion Python
real dentro de un contenedor Docker que ejecuta `systemd` como PID 1 (no un
`systemctl` simulado). Con esto se reproducen en la propia maquina, sin tocar
un servidor real, los conceptos centrales del post:

- Habilitar (`systemctl enable`) e iniciar un servicio en el arranque
  (`WantedBy=multi-user.target`).
- Politica de reinicio automatico `Restart=on-failure` con
  `StartLimitIntervalSec` / `StartLimitBurst` para evitar bucles de reinicio
  infinitos.
- Hardening basico del unit file (`NoNewPrivileges`, `PrivateTmp`).
- Logs estructurados via `journald` (`StandardOutput=journal`) consultables
  con `journalctl -u webapp.service`.
- Comandos de troubleshooting: `systemctl status`, `systemctl is-active`,
  `systemctl is-enabled`, `systemd-analyze`.

## Requisitos

- Docker Engine con soporte de Compose v2 (`docker compose ...`).
- Linux como host (el contenedor necesita acceso a `/sys/fs/cgroup` en modo
  `--privileged`; en Docker Desktop para Mac/Windows esto puede no funcionar
  igual por la capa de virtualizacion adicional).
- Sin dependencias pagas ni cuentas externas.

## Estructura

```
gestion-servicios-con-systemd/
|-- Dockerfile           # Ubuntu 22.04 + systemd corriendo como init (PID 1)
|-- docker-compose.yml    # Levanta el contenedor en modo privileged con cgroups
|-- webapp.service         # Unit file de systemd para la app de ejemplo
|-- app/server.py          # Servidor HTTP minimo gestionado por el servicio
`-- demo.sh                # Ejecuta la demo completa paso a paso
```

## Pasos para correrlo

Desde este directorio:

```bash
chmod +x demo.sh
./demo.sh
```

El script hace, en orden:

1. `docker compose up -d --build`: construye la imagen (Ubuntu + systemd) y
   levanta el contenedor. El `ENTRYPOINT`/`CMD` es `/sbin/init`, es decir,
   systemd arranca como PID 1 igual que en una VM real.
2. Espera a que `systemctl is-system-running` reporte `running` o
   `degraded` (en contenedores es normal que algunas unidades de hardware
   queden `degraded`, no afecta a la demo).
3. Muestra `systemctl status webapp.service`: el servicio ya esta activo
   porque quedo `enable`d durante el build y `multi-user.target` lo arranca.
4. Hace `curl http://localhost:8080/` contra la app real.
5. Verifica `systemctl is-active` / `is-enabled`.
6. Llama a `curl http://localhost:8080/crash`, que mata el proceso con
   `exit(1)`, y muestra como systemd lo reinicia solo por `Restart=on-failure`.
7. Muestra los logs estructurados con `journalctl -u webapp.service`.
8. Corre `systemd-analyze` para ver el tiempo de arranque del sistema.

Para limpiar todo al terminar:

```bash
docker compose down
```

### Comandos manuales (sin el script)

Si preferis ir paso a paso vos mismo, una vez que el contenedor esta arriba
(`docker compose up -d --build`):

```bash
docker exec systemd-demo systemctl status webapp.service
docker exec systemd-demo systemctl restart webapp.service
docker exec systemd-demo journalctl -u webapp.service -f
```

(`Ctrl+C` para salir del `-f`).

## Salida esperada

Al ejecutar `./demo.sh` deberias ver, entre otras cosas:

```
== 3) Estado del servicio ...
* webapp.service - Demo Web Service (ejemplo del post gestion de servicios con systemd)
     Loaded: loaded (/etc/systemd/system/webapp.service; enabled; ...)
     Active: active (running) since ...
   Main PID: 123 (python3)
      Tasks: 1
     Memory: ...
        CPU: ...

== 4) Probar el servicio HTTP ==
OK - webapp gestionada por systemd

== 5) systemctl is-active / is-enabled ==
active
enabled

== 6) Provocar un fallo y observar Restart=on-failure ==
Forzando caida del proceso...
* webapp.service - Demo Web Service ...
     Active: active (running) since ...   <- distinto PID, systemd lo reinicio solo

== 7) Logs estructurados con journalctl ==
... webapp escuchando en :8080 (PID gestionado por systemd)
... Forzando caida del proceso...
... webapp escuchando en :8080 (PID gestionado por systemd)
```

El punto clave a observar en el paso 6: el `Main PID` cambia despues del
`/crash`, confirmando que `Restart=on-failure` reinicio el proceso sin
intervencion manual, tal como se explica en el post.
