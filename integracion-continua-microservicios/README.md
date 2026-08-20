# Pipeline de CI para microservicios (mini ejemplo)

Post: [Guia Completa de Integracion continua en microservicios](https://www.devopsfreelance.pro/blog/posts/integracion-continua-microservicios/)

## Que demuestra

El post describe la piramide de pruebas para microservicios: pruebas unitarias
rapidas y aisladas, pruebas de integracion contra dependencias reales (no
mocks) y pruebas de contrato que validan la interfaz publica de un servicio.

Este ejemplo implementa un `payment-service` minimo (Flask + Postgres) y un
script `pipeline.sh` que ejecuta, en orden y con abort-on-fail, las mismas
etapas que aparecen en el pipeline YAML del post:

```
build -> unit-test -> integration-test -> contract-test
```

- **unit-test**: prueba la funcion `calculate_fee()` en aislamiento total,
  sin levantar el servicio ni la base de datos.
- **integration-test**: golpea el endpoint `/pay` del servicio real,
  corriendo contra un Postgres real levantado con docker compose (el mismo
  patron que el post ilustra con `testcontainers`, aqui con docker compose
  para no requerir dependencias extra).
- **contract-test**: valida que la respuesta de `/pay` cumple el contrato
  publicado (campos y tipos), independientemente de los valores concretos.
  Es la version simplificada de lo que hacen Pact o Spring Cloud Contract.

## Requisitos

- Docker y Docker Compose (plugin `docker compose`, no `docker-compose`)
- Python 3.11+ con `venv` disponible
- `curl`

No se necesitan cuentas ni credenciales de ningun proveedor.

## Como correrlo

Desde este directorio:

```bash
./pipeline.sh
```

El script:

1. Construye la imagen del servicio (`docker compose build`).
2. Crea un entorno virtual local e instala `pytest`/`requests` para correr
   las pruebas unitarias sin depender de Docker.
3. Corre las pruebas unitarias (`pytest -m unit`).
4. Levanta `payment-service` + Postgres con `docker compose up -d`, espera a
   que el health check responda, y corre las pruebas de integracion
   (`pytest -m integration`).
5. Corre la prueba de contrato (`pytest -m contract`).
6. Baja los contenedores (`docker compose down -v`).

Si cualquier etapa falla, el script se detiene ahi mismo (`set -e`), igual
que un pipeline de CI real.

### Correr una sola etapa manualmente

Pruebas unitarias, sin Docker:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install flask psycopg2-binary pytest requests
pytest -m unit -q
```

Servicio + base de datos reales, para probar `/pay` a mano:

```bash
docker compose up -d
curl -s http://localhost:8080/health
curl -s -X POST http://localhost:8080/pay \
  -H "Content-Type: application/json" \
  -d '{"amount": 100.00, "customer_id": "test-123"}'
docker compose down -v
```

## Salida esperada

```
== Stage: build ==
[+] Building ...

== Stage: unit-test (rapida, sin dependencias) ==
...
3 passed in 0.02s

== Stage: integration-test (servicio + Postgres reales) ==
Esperando a que payment-service este listo...
...
2 passed in 0.3s

== Stage: contract-test (valida el contrato de /pay) ==
...
1 passed in 0.1s

== Pipeline OK: todas las etapas pasaron ==
```

Y la llamada manual a `/pay` devuelve algo como:

```json
{
  "id": 1,
  "customer_id": "test-123",
  "amount": 100.0,
  "fee": 2.0,
  "status": "completed"
}
```

## Archivos

- `payment_service.py` - servicio Flask minimo con logica de negocio
  (`calculate_fee`) separada del transporte HTTP.
- `Dockerfile` - imagen del servicio.
- `docker-compose.yml` - servicio + Postgres real.
- `test_pipeline.py` - pruebas unitarias, de integracion y de contrato
  (marcadas con `@pytest.mark.unit` / `.integration` / `.contract`).
- `pipeline.sh` - orquesta las etapas del pipeline en orden.
