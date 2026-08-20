# Disaster Recovery en Cloud: simulacion practica de RTO y RPO

Ejemplo de codigo que acompana al post [Disaster Recovery en Cloud: Guía Completa para Equipos DevOps](https://www.devopsfreelance.pro/blog/posts/disaster-recovery-cloud/).

## Que demuestra este ejemplo

El post describe el nivel de servicio **Backup y Restore** (el mas basico de
los cuatro niveles de DR) y los conceptos de **RTO** (Recovery Time
Objective) y **RPO** (Recovery Point Objective). Este ejemplo simula ese
ciclo completo contra dos buckets S3 locales (via LocalStack, sin usar una
cuenta real de AWS):

1. Se crean dos buckets: `app-datos-primario` (region "activa") y
   `app-datos-dr` (region de recuperacion).
2. Se escriben datos criticos en el bucket primario.
3. Se replica el primario hacia el bucket DR (`aws s3 sync`, equivalente
   manual a S3 Cross-Region Replication).
4. Se escriben datos nuevos **despues** del ultimo checkpoint de
   replicacion, para simular la ventana de perdida de datos real de una
   estrategia de backup periodico.
5. Se simula un desastre: se elimina el bucket primario por completo.
6. Se ejecuta el failover: se crea un bucket restaurado y se copian los
   datos desde el bucket DR.
7. Se imprime un reporte con el **RTO real** (tiempo que tomo el failover) y
   el **RPO real** (ventana entre el ultimo checkpoint de replicacion y el
   momento del desastre).

El objetivo es hacer tangible por que el RPO depende de la frecuencia de
replicacion (no del failover) y por que el RTO depende de cuanto tarda el
proceso de restauracion, tal como explica el post.

## Requisitos

- Docker y Docker Compose
- AWS CLI v2 (`aws --version`)
- `curl` (para el healthcheck de LocalStack)

No se necesita ninguna cuenta ni credencial real de AWS: LocalStack emula
S3 en tu maquina con credenciales dummy (`test`/`test`).

## Pasos para correrlo

```bash
# 1. Levantar LocalStack
docker compose up -d

# 2. Ejecutar la simulacion completa de DR
bash scripts/simulate_dr.sh

# 3. Cuando termines, apagar LocalStack
docker compose down -v
```

## Salida esperada

El script imprime cada paso con timestamp y termina con un reporte como
este (los segundos exactos varian segun tu maquina):

```
[10:15:03] Esperando a que LocalStack este listo...
[10:15:03] LocalStack listo.
[10:15:03] Creando buckets (simulando region primaria y region DR)...
[10:15:04] Buckets creados: app-datos-primario (primario), app-datos-dr (DR).
[10:15:04] Dato critico escrito en primario: clientes.json
[10:15:04] Dato critico escrito en primario: transacciones.log
[10:15:04] Replicando primario -> DR (equivalente a S3 Cross-Region Replication)...
[10:15:05] Replicacion completada. Checkpoint RPO: 10:15:05
[10:15:05] Dato critico escrito en primario: transacciones.log
[10:15:05] === SIMULANDO DESASTRE: perdida de la region primaria ===
[10:15:05] Region primaria eliminada en 10:15:05.
[10:15:05] === INICIANDO FAILOVER hacia la region DR ===
[10:15:06] Failover completado en 10:15:06.

================= REPORTE DE DISASTER RECOVERY =================
Bucket restaurado: s3://app-datos-restaurado
Objetos recuperados:
  - clientes.json
  - transacciones.log

RTO (tiempo de recuperacion, failover completo): 1s
RPO (ventana de datos potencialmente perdidos):  0s
===================================================================
```

Nota: el bucket restaurado NO contendra la segunda linea de
`transacciones.log` (la escrita despues del checkpoint de replicacion) ya
que ese dato se perdio en el desastre simulado. Podes verificarlo con:

```bash
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
aws --endpoint-url=http://localhost:4566 s3 cp \
  s3://app-datos-restaurado/transacciones.log - \
  --region us-east-1
```

## Relacion con el codigo Terraform del post

El post muestra un `aws_s3_bucket` con `replication_configuration` para
replicar un bucket real de AWS entre `us-east-1` y `us-west-2`. Ese
Terraform requiere una cuenta AWS real y roles IAM. Este ejemplo reproduce
el mismo concepto (replicacion entre dos "regiones" + failover) de forma
100% local y gratuita, para poder experimentar con RTO/RPO sin costo.

## Limpieza

```bash
docker compose down -v
```

Esto detiene LocalStack y borra el volumen con los datos simulados.
