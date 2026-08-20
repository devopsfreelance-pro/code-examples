# Troubleshooting Avanzado en Linux - Laboratorio práctico

Post relacionado: [Troubleshooting Avanzado en Linux: Guía Definitiva 2026](https://www.devopsfreelance.pro/blog/posts/troubleshooting-avanzado-linux/)

## Qué demuestra este ejemplo

El post explica una metodología sistemática de troubleshooting (baseline,
formulación de hipótesis, validación con evidencia) usando herramientas como
`perf`, `iostat`, `journalctl` y `tcpdump`. Muchas de esas herramientas
requieren acceso privilegiado al kernel del host, así que este laboratorio
reproduce el mismo flujo de diagnóstico dentro de contenedores Docker
normales, sin privilegios especiales:

- Un contenedor (`app`) ejecuta una aplicación Python que simula, a
  propósito, los síntomas típicos descritos en el post: un **memory leak**
  lento, **picos periódicos de CPU** y **logs estructurados** con eventos
  `INFO`/`WARN`/`ERROR`/`CRITICAL`.
- Un script (`diagnose.sh`) aplica la metodología **USE** (Utilization,
  Saturation, Errors) del post: mide utilización de recursos con
  `docker stats` (equivalente a `top`/`iostat`), identifica el proceso que
  más memoria consume con `ps aux --sort=-%mem`, y corre un pipeline de
  análisis de logs con `grep`/`awk`/`sort`/`uniq -c` equivalente al ejemplo
  de `journalctl` del post, para correlacionar causas de error.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- Bash

No se necesitan permisos privilegiados, herramientas de kernel (`perf`,
`eBPF`, `blktrace`) ni cuentas de terceros.

## Pasos para ejecutarlo

1. Construir y levantar el contenedor de ejemplo:

```bash
docker compose up -d --build
```

2. Esperar unos 20-30 segundos para que la app genere tráfico simulado y al
   menos un pico de CPU (ocurre cada ~15 segundos):

```bash
sleep 30
```

3. Correr el script de diagnóstico:

```bash
chmod +x diagnose.sh
./diagnose.sh
```

4. (Opcional) Dejarlo corriendo unos minutos y volver a ejecutar
   `./diagnose.sh` para ver cómo crece `VmRSS` (el memory leak) hasta que el
   contenedor se acerca al límite de memoria (`mem_limit: 150m` en
   `docker-compose.yml`), tal como se describe en la sección de análisis de
   memoria del post.

5. Para limpiar el entorno:

```bash
docker compose down
```

## Salida esperada

El script imprime 5 secciones. Un ejemplo representativo:

```
==============================================
1) Linea base de utilizacion (metodologia USE)
==============================================
CONTAINER ID   NAME                        CPU %     MEM USAGE / LIMIT     MEM %
a1b2c3d4e5f6   troubleshooting-demo-app    2.10%     18.5MiB / 150MiB      12.33%

==============================================
2) Procesos ordenados por uso de memoria (leak)
==============================================
USER    PID  %CPU %MEM    VSZ   RSS TTY   STAT START   TIME COMMAND
root      1   3.2  8.1  35000 18500 ?     Ssl  10:00   0:02 python3 -u leaky_app.py

==============================================
3) Memoria detallada del proceso principal
==============================================
VmSize:    35120 kB
VmData:    28900 kB
VmRSS:     18500 kB

==============================================
4) Analisis de logs: errores y criticos (ultimos 200 eventos)
   equivalente a: journalctl -p err
==============================================
2026-02-14 10:00:12,001 ERROR pid=1 request=POST /api/payments status=500 latency_ms=1240 causa=timeout_backend
2026-02-14 10:00:20,003 CRITICAL pid=1 request=GET /api/health status=503 latency_ms=15 causa=pool_conexiones_agotado

==============================================
5) Correlacion de patrones: frecuencia de causas de error
   equivalente al pipeline journalctl | grep | awk | sort | uniq -c del post
==============================================
      4 causa=timeout_backend
      2 causa=pool_conexiones_agotado

Diagnostico completado.
```

Los valores exactos (PID, timestamps, cantidades) varían en cada corrida
porque la app genera eventos aleatorios, pero la estructura y el tipo de
hallazgos (memoria creciendo, errores correlacionados por causa) se
mantienen, ilustrando el flujo de diagnóstico descrito en el post.

## Estructura de archivos

```
troubleshooting-avanzado-linux/
├── README.md
├── docker-compose.yml       # define el contenedor de ejemplo con limite de memoria
├── diagnose.sh               # aplica la metodologia USE + analisis de logs
└── app/
    ├── Dockerfile
    └── leaky_app.py           # simula memory leak, picos de CPU y logs estructurados
```
