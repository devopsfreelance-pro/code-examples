# eBPF en accion: observabilidad de red y deteccion de amenazas en tiempo real

Ejemplo de codigo que acompana al post [eBPF: Revolución en Observabilidad y Seguridad 2026](https://www.devopsfreelance.pro/blog/posts/ebpf-observabilidad-seguridad/).

## Que demuestra

El post explica que eBPF permite dos cosas sin instrumentar aplicaciones ni modificar el kernel: capturar telemetria del sistema (observabilidad) y aplicar controles de seguridad en tiempo real desde el propio kernel (security). Este ejemplo muestra ambas caras con las mismas herramientas que menciona el post:

1. **Observabilidad**: un script [bpftrace](https://github.com/bpftrace/bpftrace) (`bpftrace/tcp_connections.bt`) enganchado al tracepoint estable `sock:inet_sock_set_state` del kernel, que rastrea cada conexion TCP saliente del sistema (proceso, PID, IP y puerto destino) sin tocar el codigo de ninguna aplicacion.
2. **Security**: [Falco](https://falco.org/) corriendo con su motor `modern_ebpf` (`docker-compose.yml`), detectando en tiempo real dos comportamientos anomalos: lectura de un archivo sensible del host (`/etc/shadow`) desde un contenedor, y apertura de una shell interactiva dentro de un contenedor en ejecucion. Ambas son reglas por defecto de Falco, el mismo proyecto que el post menciona como ejemplo de deteccion de amenazas basada en eBPF.

## Requisitos

- Linux con kernel >= 5.8 y soporte BTF (la gran mayoria de distros recientes: Ubuntu 22.04+, Debian 12+, Fedora 36+). El motor `modern_ebpf` de Falco lo necesita para no requerir compilar un driver.
- [Docker](https://docs.docker.com/get-docker/) corriendo localmente, con permiso para contenedores `privileged`.
- Acceso a `/sys/kernel/debug` y `/sys/fs/bpf` en el host (por defecto disponibles en Linux; no funciona dentro de Docker Desktop en macOS/Windows porque ahi no hay un kernel Linux real expuesto).

No se necesita ninguna cuenta ni servicio pago: todo corre en contenedores locales sobre tu propio kernel.

**No corre en runners de CI genericos (GitHub Actions, GitLab CI, etc.)**: aunque el runner sea Linux y el contenedor de Falco se levante en modo `privileged`, la carga de los programas eBPF del motor `modern_ebpf` depende de que la relocacion CO-RE coincida exactamente con el BTF del kernel del runner; en la practica esto falla con errores de inicializacion (`scap_init`) fuera de una maquina donde controlas el kernel. Este ejemplo esta pensado para correrlo en tu propia maquina Linux, no en pipelines de CI.

## Archivos

- `docker-compose.yml` — Levanta Falco (`falcosecurity/falco-no-driver`) en modo privilegiado con el motor eBPF `modern_ebpf`, con salida en JSON.
- `trigger-suspicious-activity.sh` — Dispara los dos eventos sospechosos (lectura de `/etc/shadow`, shell inesperada en un contenedor) para que Falco los detecte.
- `bpftrace/tcp_connections.bt` — Programa eBPF en bpftrace que rastrea conexiones TCP salientes del sistema.

## Pasos para correrlo

### 1. Deteccion de amenazas en tiempo real con Falco (eBPF security)

```bash
cd ebpf-observabilidad-seguridad

# Levantar Falco con el motor eBPF
docker compose up -d

# Esperar a que termine de inicializar el probe eBPF (unos segundos)
sleep 5
docker logs falco-ebpf-demo --tail 20

# Dar permisos de ejecucion al script de disparo (una sola vez)
chmod +x trigger-suspicious-activity.sh

# Disparar las actividades sospechosas
./trigger-suspicious-activity.sh

# Ver las alertas generadas por eBPF en el kernel, sin agentes en las apps
docker logs falco-ebpf-demo --tail 50
```

#### Limpieza

```bash
docker compose down
```

### 2. Observabilidad de red con bpftrace (eBPF observability)

```bash
cd ebpf-observabilidad-seguridad

# Correr el script bpftrace dentro del contenedor oficial, con acceso al kernel del host
docker run --rm -it --privileged --pid=host \
  -v /sys/kernel/debug:/sys/kernel/debug:rw \
  -v "$(pwd)/bpftrace:/bpftrace" \
  quay.io/iovisor/bpftrace:latest \
  bpftrace /bpftrace/tcp_connections.bt
```

Mientras el script corre, abrí una segunda terminal y generá trafico saliente, por ejemplo `curl https://www.devopsfreelance.pro` o `curl https://example.com`. Cortá con `Ctrl+C` cuando termines.

## Salida esperada

### Falco (seguridad)

```
== 1) Leyendo /etc/shadow desde un contenedor busybox ==
== 2) Abriendo una shell dentro de un contenedor nginx ==
hola desde una shell inesperada

Listo. Revisa las alertas con:
  docker logs falco-ebpf-demo --tail 50
```

Y en `docker logs falco-ebpf-demo`, dos alertas JSON generadas por el motor eBPF, con forma similar a:

```json
{"output":"20:14:03.221 Warning Sensitive file opened for reading by non-trusted program (file=/etc/shadow ...)", "priority":"Warning", "rule":"Read sensitive file untrusted", ...}
{"output":"20:14:05.114 Notice A shell was spawned in a container ...", "priority":"Notice", "rule":"Terminal shell in container", ...}
```

### bpftrace (observabilidad)

```
Attaching 2 probes...
Rastreando conexiones TCP salientes (Ctrl+C para salir)...
PID    PROCESO          IP DESTINO       PUERTO
48213  curl             93.184.216.34    443
```

## Notas

- `falcosecurity/falco-no-driver` no incluye el modulo de kernel legacy: usa el motor `modern_ebpf`, mas simple de correr en contenedores porque no requiere descargar ni compilar un driver contra la version exacta del kernel del host.
- Si tu kernel no soporta `modern_ebpf` (kernel < 5.8 o sin BTF), Falco no podra levantar el probe y el contenedor terminara en error; en ese caso el post explica la alternativa (motor con kernel module o eBPF probe clasico), fuera del alcance de este mini-ejemplo.
