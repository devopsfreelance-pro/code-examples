FROM alpine:3.20

RUN apk add --no-cache stress-ng procps

# stress-ng intentará reservar 150M de RAM; el contenedor se levantará
# con un límite de memoria (cgroup) de 100M para forzar un OOM-kill
# y demostrar que el kernel realmente aplica el límite.
CMD ["stress-ng", "--vm", "1", "--vm-bytes", "150M", "--vm-keep", "--timeout", "20s", "-v"]
