# Cost Allocation Showback en Cloud - Ejemplo Ejecutable

Post: https://www.devopsfreelance.pro/blog/posts/cost-allocation-showback-cloud/

## Que demuestra

El post explica, en el "Caso 2 - Empresa Enterprise", como distribuir el costo
de un cluster de Kubernetes compartido entre varios equipos en proporcion al
consumo real de CPU/memoria (patron `SharedCostAllocator`). Este ejemplo
reproduce esa idea en miniatura, sin necesidad de un cluster real ni de una
cuenta cloud:

- `docker-compose.yml` levanta un "cluster compartido" simulado con 3
  contenedores (`team-checkout`, `team-payments`, `team-search`) que consumen
  CPU en distinta proporcion, mas `cAdvisor` (mide el consumo de cada
  contenedor) y `Prometheus` (scrapea esas metricas).
- `allocate_costs.py` consulta Prometheus, calcula el `cpu_share` de cada
  contenedor y distribuye un costo mensual ficticio del cluster
  proporcionalmente a ese uso, exactamente como haria un chargeback/showback
  real para un servicio compartido.
- `team_mapping.json` es la "taxonomia de etiquetado" del post: mapea cada
  contenedor tecnico a un equipo y un cost center de negocio.

Para simplificar el ejemplo se distribuye solo por CPU (en el post se pondera
CPU y memoria por igual); el mismo enfoque se extiende agregando
`container_memory_working_set_bytes` a `allocate_costs.py`.

## Requisitos

- Docker y Docker Compose v2 (`docker compose version`)
- Python 3.8+ (usa solo la libreria estandar, no requiere `pip install`)
- Linux recomendado (cAdvisor necesita acceso de solo lectura a `/var/lib/docker`
  y `/sys` del host; en Docker Desktop para Mac/Windows algunas metricas de
  cAdvisor pueden no estar disponibles de la misma forma)

## Pasos para correrlo

1. Levantar el cluster simulado (Prometheus, cAdvisor y los 3 "equipos"):

```bash
cd cost-allocation-showback-cloud
docker compose up -d
```

2. Esperar 1-2 minutos para que Prometheus acumule suficientes muestras de
   `rate()`:

```bash
sleep 90
```

3. (Opcional) Verificar que Prometheus ve los 3 contenedores:

```bash
curl -s 'http://localhost:9090/api/v1/query?query=up' | python3 -m json.tool
```

4. Calcular la distribucion de costos:

```bash
python3 allocate_costs.py
```

Para probar con otro costo mensual del cluster:

```bash
CLUSTER_MONTHLY_COST=5000 python3 allocate_costs.py
```

5. Apagar todo:

```bash
docker compose down
```

## Salida esperada

`team-checkout` corre un loop sin pausas (mayor uso de CPU), `team-payments`
hace pausas cortas y `team-search` pausas largas, asi que el reparto de costo
deberia quedar aproximadamente en ese orden (los numeros exactos varian segun
la maquina):

```
Costo mensual del cluster compartido: $3,000.00

Team           Cost Center       CPU share    Costo asignado
------------------------------------------------------------
Checkout       CC-1001               55.0%          $1,650.00
Payments       CC-1002               30.0%            $900.00
Search         CC-1003               15.0%            $450.00
```

Si ves `No hay uso de CPU medido todavia`, espera un poco mas: Prometheus
necesita al menos un par de scrapes (`scrape_interval: 5s`) dentro de la
ventana `[2m]` que usa la query.

## Notas

- No se usan servicios pagos: todo corre en contenedores locales.
- `PROMETHEUS_URL`, `CLUSTER_MONTHLY_COST` y `PROM_RANGE` son configurables
  por variable de entorno en `allocate_costs.py`.
- Este ejemplo es una simplificacion didactica del pipeline de CUR (Cost and
  Usage Reports) del post; no sustituye la integracion real con AWS Cost
  Explorer / Cost and Usage Reports.
