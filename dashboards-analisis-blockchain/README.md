# Blockchain Dashboard con Prometheus + Grafana

Ejemplo de código para el post [Blockchain Dashboard: Guía Completa de Visualización 2026](https://www.devopsfreelance.pro/blog/posts/dashboards-analisis-blockchain/).

## Qué demuestra

La arquitectura de capas descrita en el post (exporter -> Prometheus -> Grafana)
funcionando de punta a punta en tu máquina:

1. Un **exporter en Python** (`exporter/exporter.py`) expone métricas estilo
   Ethereum (`ethereum_block_number`, `ethereum_gas_price_gwei`,
   `ethereum_pending_tx`) en formato Prometheus vía `prometheus_client`, igual
   que el snippet del post. Para no depender de una API key de Infura/Alchemy
   ni de un nodo real, simula las lecturas del nodo (número de bloque
   incremental, gas price y transacciones pendientes aleatorios) mediante
   `simulate_node_read()`. La función está aislada justo ahí: si tenés un
   endpoint RPC propio, la reemplazás por llamadas reales de `web3.py` y el
   resto del pipeline (Prometheus, Grafana) no cambia.
2. **Prometheus** scrapea el exporter cada 5 segundos (`prometheus.yml`).
3. **Grafana** consume Prometheus como datasource para graficar las métricas
   (gas price, bloques, tx pendientes) igual que el panel JSON del post.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- Ningún servicio pago ni API key: todo corre local con contenedores.

## Pasos para correrlo

```bash
cd dashboards-analisis-blockchain
docker compose up -d --build
```

Verificar que el exporter está publicando métricas:

```bash
curl -s http://localhost:8000/metrics | grep ethereum_
```

Salida esperada (los valores cambian en cada scrape):

```
# HELP ethereum_block_number Número de bloque actual
# TYPE ethereum_block_number gauge
ethereum_block_number 21000001.0
# HELP ethereum_gas_price_gwei Precio de gas en Gwei
# TYPE ethereum_gas_price_gwei gauge
ethereum_gas_price_gwei 42.17
# HELP ethereum_pending_tx Transacciones pendientes
# TYPE ethereum_pending_tx gauge
ethereum_pending_tx 1873.0
```

Verificar que Prometheus ve el target `UP`:

```
http://localhost:9090/targets
```

### Configurar el dashboard en Grafana

1. Abrir `http://localhost:3000` (usuario `admin`, contraseña `admin`).
2. Ir a **Connections > Data sources > Add data source > Prometheus**.
3. URL: `http://prometheus:9090` (nombre del servicio dentro de la red de
   Docker Compose) y guardar (**Save & test** debe dar OK).
4. Crear un panel nuevo con la query `ethereum_gas_price_gwei` (tipo Time
   series) para ver la tendencia de gas fees en tiempo real, tal como
   describe el post en la sección "Implementación Práctica con Grafana
   Ethereum".

## Apagar el entorno

```bash
docker compose down
```

## Notas

- El exporter simula datos para que el ejemplo funcione sin credenciales.
  En producción reemplazá `simulate_node_read()` por llamadas reales con
  `web3.py` contra un nodo propio o un proveedor (Infura, Alchemy,
  QuickNode), como se explica en el post.
- Las credenciales de Grafana (`admin`/`admin`) son solo para este entorno
  local. Cambiarlas antes de exponer Grafana fuera de tu máquina.
