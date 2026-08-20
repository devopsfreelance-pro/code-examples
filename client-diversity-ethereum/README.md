# Client Diversity en Ethereum: calculadora de riesgo + alertas Prometheus

Post: [Guía Definitiva de Client Diversity en Ethereum para DevOps](https://www.devopsfreelance.pro/blog/posts/client-diversity-ethereum/)

## Qué demuestra este ejemplo

Correr un nodo real de Ethereum (Geth, Nethermind, Lighthouse, etc.) requiere
sincronizar cientos de GB de estado, algo inviable para un ejemplo local. En
cambio, este mini-proyecto ilustra el concepto central del post -la
**client diversity como práctica operativa medible**- de dos formas:

1. `diversity_calculator.py`: dado un JSON con la cuota de mercado de cada
   cliente (execution layer y consensus layer), calcula el índice
   Herfindahl-Hirschman (HHI) de concentración y clasifica el riesgo según
   los umbrales reales que usa la comunidad Ethereum (33% / 50% / 66%,
   este último el umbral de supermayoría de Casper FFG mencionado en el
   post).
2. `diversity_exporter.py` + `prometheus.yml` + `prometheus_alerts.yml`:
   exponen esa misma distribución como métricas Prometheus
   (`ethereum_client_share_percent`) y disparan alertas automáticas cuando
   un cliente supera esos umbrales, tal como se describe en la sección
   "Monitorear la salud de los clientes" del post.

Los datos de `sample_distribution.json` son aproximados (inspirados en el
tipo de reporte que publica [clientdiversity.org](https://clientdiversity.org/)),
no una foto exacta del mainnet actual. Reemplazalos por datos reales si
querés un análisis vigente.

## Requisitos

- Python 3.9+ (para correr solo la calculadora, sin Docker)
- Docker + Docker Compose (para levantar el exporter + Prometheus con alertas)

## Paso 1: calculadora de riesgo (sin Docker)

```bash
python3 diversity_calculator.py sample_distribution.json
```

Salida esperada (resumida):

```
Analisis de client diversity: Distribucion de mercado de ejemplo...

== Execution Layer ==
  geth          44.2%  ######################
  nethermind    29.8%  ##############
  besu          13.5%  ######
  erigon        12.5%  ######
  Cliente dominante : geth (44.2%)
  Indice HHI        : 0.318 (0=diverso, 1=monopolio)
  Nivel de riesgo   : MEDIO

== Consensus Layer ==
  prysm         38.0%  ###################
  ...
  Nivel de riesgo   : MEDIO
```

El script devuelve exit code `2` si algún cliente entra en riesgo ALTO o
CRITICO (>=50%), útil para usarlo como gate en un pipeline de CI que audite
la distribución de tu flota de nodos.

Probá también con un escenario de riesgo crítico:

```bash
cat > /tmp/riesgo-critico.json <<'EOF'
{
  "description": "Escenario de riesgo critico (Prysm > 66%)",
  "consensus_layer": { "prysm": 68.0, "lighthouse": 20.0, "teku": 7.0, "nimbus": 5.0 }
}
EOF
python3 diversity_calculator.py /tmp/riesgo-critico.json; echo "exit: $?"
```

Debería mostrar `Nivel de riesgo : CRITICO` y `exit: 2`.

## Paso 2: exporter + Prometheus con alertas (con Docker)

```bash
docker compose up -d
```

Esto levanta:

- `diversity-exporter` en `http://localhost:9877/metrics`: sirve
  `sample_distribution.json` como métricas Prometheus.
- `prometheus` en `http://localhost:9090`: scrapea el exporter cada 15s y
  evalúa `prometheus_alerts.yml`.

Verificar el exporter:

```bash
curl http://localhost:9877/metrics
```

Salida esperada:

```
# HELP ethereum_client_share_percent Cuota de mercado de un cliente Ethereum
# TYPE ethereum_client_share_percent gauge
ethereum_client_share_percent{layer="execution",client="geth"} 44.2
ethereum_client_share_percent{layer="execution",client="nethermind"} 29.8
...
```

Ver las alertas cargadas en Prometheus: abrir `http://localhost:9090/alerts`
en el navegador (o `curl -s http://localhost:9090/api/v1/rules | grep alert`).
Con los datos de ejemplo (máximo 44.2% en execution, 38% en consensus)
ninguna alerta debería estar en estado `firing` todavía; para verla disparar,
editá `sample_distribution.json` subiendo algún cliente por encima de 66% y
esperá al próximo scrape (15s) más los 5 minutos de `for:` configurados en
`prometheus_alerts.yml`, o bajá ese `for:` a `0m` para probarlo más rápido.

Apagar todo:

```bash
docker compose down
```

## Archivos

- `diversity_calculator.py`: calculadora de riesgo standalone (HHI + umbrales).
- `diversity_exporter.py`: exporter HTTP minimalista en Python estándar (sin
  dependencias) que sirve `/metrics` en formato Prometheus.
- `sample_distribution.json`: distribución de ejemplo de execution y
  consensus layer.
- `prometheus.yml`: config de scrape para el exporter, más carga de reglas.
- `prometheus_alerts.yml`: reglas de alerta para los umbrales 33/50/66%.
- `docker-compose.yml`: levanta exporter + Prometheus conectados entre sí.

No hay secretos ni cuentas que configurar: todo corre localmente.
