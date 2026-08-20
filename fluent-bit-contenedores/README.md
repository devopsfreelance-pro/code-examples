# Fluent Bit para contenedores: pipeline de parsing y routing

Ejemplo ejecutable que acompaña al post [Guía Completa de Fluent bit para contenedores](https://www.devopsfreelance.pro/blog/posts/fluent-bit-contenedores/).

## Qué demuestra

Un pipeline completo de Fluent Bit corriendo en Docker, sin necesidad de un cluster de Kubernetes:

- Un contenedor `app-log-generator` escribe logs JSON (uno por línea) a un volumen compartido, simulando los logs que un pod escribiría en `/var/log/containers/`.
- Fluent Bit hace **tail** de ese archivo, los **parsea** con el parser JSON, los **enriquece** con metadata fija (equivalente al filtro `kubernetes` que agrega labels/namespace en un cluster real) y hace **routing condicional**:
  - Todos los registros van a **stdout** (`docker compose logs fluent-bit`), como harías con `kubectl logs`.
  - Los registros con `level=error` se re-etiquetan con `rewrite_tag` y se archivan aparte en `logs-out/errors.log`, igual que en el post se enruta logs de infraestructura a S3 o logs de seguridad a CloudWatch según el tag.
- Fluent Bit expone métricas Prometheus en `http://localhost:2020/api/v1/metrics/prometheus`, las mismas que se recomiendan monitorear en la sección de tuning del post (`fluentbit_input_records_total`, `fluentbit_output_errors_total`, etc.).

## Requisitos

- Docker y Docker Compose (`docker compose version`).
- Puerto `2020` libre en localhost.

## Cómo correrlo

```bash
cd fluent-bit-contenedores
mkdir -p logs-out
docker compose up -d
```

Esperá unos 10 segundos a que el generador escriba logs y Fluent Bit los procese, luego mirá los tres destinos:

```bash
# 1. Todos los logs en stdout (formato JSON, un registro por línea)
docker compose logs fluent-bit --no-log-prefix

# 2. Solo los logs de error, archivados aparte por el filtro rewrite_tag
cat logs-out/errors.log

# 3. Métricas Prometheus expuestas por Fluent Bit
curl -s http://localhost:2020/api/v1/metrics/prometheus | grep fluentbit_output
```

Para detener y limpiar todo:

```bash
docker compose down -v
rm -f logs-out/errors.log
```

## Salida esperada

En `docker compose logs fluent-bit` vas a ver líneas como:

```
{"date":1787238348.0,"time":"2026-08-20T15:05:48.000Z","level":"info","message":"request procesado correctamente","request_id":"req-3","container_name":"demo-app","environment":"local"}
```

En `logs-out/errors.log` solo van a aparecer los registros con `level=error` (aproximadamente 1 de cada 5, generados a propósito por el script):

```
{"time":"2026-08-20T15:05:50.000Z","level":"error","message":"fallo al conectar con la base de datos","request_id":"req-5","container_name":"demo-app","environment":"local"}
```

`curl localhost:2020/api/v1/metrics/prometheus` va a devolver contadores tipo `fluentbit_input_records_total`, `fluentbit_filter_drop_records_total` (los registros no-error que el filtro `rewrite_tag` descarta del tag `app.errors`) y `fluentbit_output_errors_total`, las métricas que el post recomienda monitorear para detectar backpressure.

## Archivos

- `docker-compose.yml`: define el generador de logs y el contenedor de Fluent Bit, con un volumen compartido para los logs de entrada y otro para la salida a archivo.
- `fluent-bit.conf`: pipeline completo (`INPUT` tail → `FILTER` modify → `FILTER` rewrite_tag → `OUTPUT` stdout + `OUTPUT` file).
- `parsers.conf`: parser JSON usado para estructurar los logs de entrada.

No hay secretos ni cuentas cloud involucradas: todo corre en local con imágenes públicas (`alpine:3.20`, `cr.fluentbit.io/fluent/fluent-bit:3.1`).
