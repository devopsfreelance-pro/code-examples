# Testing Pipeline con pirámide de pruebas (unitarias + integración)

Ejemplo de código para el post [Automated Testing en Pipelines: Guía Completa 2025](https://www.devopsfreelance.pro/blog/posts/testing-automation-pipelines/).

## Qué demuestra

Un servicio mínimo de inventario (`app.py`) diseñado para que su lógica de
negocio (`InventoryService`) esté completamente separada del acceso a datos
(`StockRepository`, que habla con Redis). Esa separación es la que hace
posible construir la pirámide de testing descrita en el post:

- **`test_unit.py`**: pruebas unitarias rápidas y numerosas (la base de la
  pirámide). No tocan Redis: usan un repositorio falso en memoria.
- **`test_integration.py`**: pruebas de integración (el nivel medio/cúspide
  de la pirámide). Ejercitan `StockRepository` contra un Redis real levantado
  con Docker.
- **`run_pipeline.sh`**: simula un testing pipeline de verdad, ejecutando las
  etapas en el orden que describe el post (análisis estático → unitarias →
  integración) y **deteniéndose apenas falla una etapa**, sin desperdiciar
  tiempo en las siguientes.
- **`ci-pipeline-example.yml`**: el mismo pipeline trasladado a GitHub
  Actions, con jobs encadenados (`needs:`) que reproducen el mismo fail-fast.
  Es solo referencia; no se ejecuta en este repo.

## Requisitos

- Python 3.10+
- Docker y Docker Compose (para levantar Redis en las pruebas de integración)

## Cómo correrlo

```bash
cd testing-automation-pipelines

# 1. Crear entorno virtual e instalar dependencias
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Correr solo las pruebas unitarias (no requieren Docker, corren en segundos)
python3 -m pytest test_unit.py -v

# 3. Levantar Redis para las pruebas de integración
docker compose up -d
docker compose ps   # esperar a que el healthcheck diga "healthy"

# 4. Correr el pipeline completo (análisis estático + unitarias + integración)
chmod +x run_pipeline.sh
./run_pipeline.sh

# 5. Al terminar, apagar Redis
docker compose down
```

## Salida esperada

Al ejecutar `./run_pipeline.sh` con Redis levantado, la salida es similar a:

```
=== Etapa 1/3: análisis estático (pyflakes) ===

=== Etapa 2/3: pruebas unitarias (rápidas, sin dependencias externas) ===
test_unit.py::test_restock_incrementa_stock_desde_cero PASSED
test_unit.py::test_restock_acumula_stock_existente PASSED
test_unit.py::test_restock_rechaza_cantidad_no_positiva PASSED
test_unit.py::test_reserve_descuenta_stock_disponible PASSED
test_unit.py::test_reserve_falla_si_no_hay_stock_suficiente PASSED
test_unit.py::test_reserve_rechaza_cantidad_no_positiva PASSED
6 passed

=== Etapa 3/3: pruebas de integración (requieren Redis) ===
test_integration.py::test_restock_y_reserve_persisten_en_redis PASSED
1 passed

Pipeline completo: todas las etapas pasaron.
```

Si Redis no está levantado, la prueba de integración se salta (`SKIPPED`) con
un mensaje indicando cómo levantarlo, en vez de fallar de forma confusa.

Si rompés algo en `app.py` (por ejemplo, permitís `reserve` con stock
negativo), las pruebas unitarias fallan en la etapa 2 y el script corta ahí:
nunca llega a levantar ni consultar Redis, tal como describe el post sobre
pipelines que respetan la pirámide de testing y aplican fail-fast.

## Nota sobre el YAML de GitHub Actions

`ci-pipeline-example.yml` no está en `.github/workflows/` a propósito: es un
archivo de referencia para copiar a un repo real, no un workflow activo de
este repositorio.
