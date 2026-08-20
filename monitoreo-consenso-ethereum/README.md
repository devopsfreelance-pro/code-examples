# Monitoreo de Consenso en Ethereum: ejemplo ejecutable

Post: [Guía Completa de Monitoreo de consenso en Ethereum](https://www.devopsfreelance.pro/blog/posts/monitoreo-consenso-ethereum/)

## Qué demuestra este ejemplo

Un stack local mínimo con el enfoque de monitoreo de validadores PoS que describe el post:

- **Exportador de métricas de validadores** (`exporter.py`): reimplementa el script Python del post que consulta la API de un nodo Beacon (`validator_balance`, `validator_status`, `attestation_effectiveness`). Como correr un nodo Beacon real requiere sincronizar Ethereum (días de descarga y GBs de disco), acá se simulan 3 validadores igual que en el ejemplo del post (índices `123456`, `123457`, `123458`), y uno de ellos (`123458`) se simula "problemático" fallando attestations la mayoría de los ticks para poder ver la alerta dispararse.
- **Scraping con Prometheus** (`prometheus.yml`): mismo job `validator_client` que usa el post, apuntando al exportador.
- **Reglas de alerta** (`validator_alerts.yml`): las dos alertas exactas del post, `ValidatorMissedAttestation` y `ValidatorOffline`.
- **Grafana** para visualizar las métricas, como recomienda el post.

No incluye Alertmanager ni notificaciones a Slack/PagerDuty (serían overkill para un mini-ejemplo); las reglas de alerta se pueden ver evaluándose y disparándose directamente en la UI de Prometheus.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- Puertos libres en tu máquina: `8081`, `9090`, `3000`

## Cómo correrlo

```bash
cd monitoreo-consenso-ethereum
docker compose up --build
```

Esperá a ver en los logs del exportador líneas como:

```
eth-validator-exporter | Validator 123458 - Balance: 32000012345 Gwei, Missed: 4, Effectiveness: 80.0%
```

### Ver las métricas crudas del exportador

```bash
curl -s http://localhost:8081/metrics | grep validator_
```

Salida esperada (valores exactos varían, son simulados):

```
validator_balance{validator_index="123456"} 3.2000012e+10
validator_balance{validator_index="123457"} 3.2000034e+10
validator_balance{validator_index="123458"} 3.1999980e+10
validator_status{validator_index="123456"} 1.0
validator_status{validator_index="123457"} 1.0
validator_status{validator_index="123458"} 1.0
attestation_effectiveness{validator_index="123456"} 97.3
attestation_effectiveness{validator_index="123457"} 98.1
attestation_effectiveness{validator_index="123458"} 65.0
validator_missed_attestations_total{validator_index="123458"} 7.0
```

### Ver el scraping y las alertas en Prometheus

Abrí http://localhost:9090/targets — el target `validator_client` debe aparecer en estado `UP`.

Abrí http://localhost:9090/alerts. Después de un par de minutos vas a ver la alerta `ValidatorMissedAttestation` en estado `pending` o `firing` para `validator_index="123458"`, mientras que `123456` y `123457` se mantienen en `inactive`.

También podés correr la query PromQL directamente en http://localhost:9090/graph:

```
increase(validator_missed_attestations_total[1h]) > 3
```

### Ver un dashboard en Grafana

Abrí http://localhost:3000 (acceso anónimo habilitado, sin login necesario; usuario admin/admin si preferís loguearte).

1. Ir a **Connections > Data sources > Add data source** y elegir **Prometheus**.
2. URL: `http://prometheus:9090` (nombre del servicio dentro de la red de docker-compose).
3. Guardar y probar (`Save & test`) — debe confirmar la conexión.
4. Ir a **Explore**, elegir la datasource Prometheus, y graficar `attestation_effectiveness` o `validator_balance` para ver las series de los 3 validadores simulados.

## Parar el stack

```bash
docker compose down
```
