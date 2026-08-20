#!/usr/bin/env bash
# Consulta rapida sobre el indice cargado por Logstash, equivalente a lo que
# harias en Kibana Discover / una visualizacion de errores 5xx.
set -euo pipefail

ES_URL="${ES_URL:-http://localhost:9200}"
INDEX="elk-demo-logs-*"

echo "== Salud del cluster =="
curl -s "${ES_URL}/_cluster/health?pretty"

echo
echo "== Documentos indexados en ${INDEX} =="
curl -s "${ES_URL}/${INDEX}/_count?pretty"

echo
echo "== Ultimos 5 eventos (por timestamp) =="
curl -s -X GET "${ES_URL}/${INDEX}/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{
        "size": 5,
        "sort": [{ "@timestamp": "desc" }],
        "_source": ["@timestamp", "clientip", "verb", "request", "response"]
      }'

echo
echo "== Requests con respuesta 5xx (busqueda de errores) =="
curl -s -X GET "${ES_URL}/${INDEX}/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{
        "query": { "range": { "response": { "gte": 500 } } },
        "_source": ["@timestamp", "clientip", "request", "response"]
      }'

echo
echo "== Conteo de requests agrupado por codigo de respuesta =="
curl -s -X GET "${ES_URL}/${INDEX}/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{
        "size": 0,
        "aggs": {
          "por_response": {
            "terms": { "field": "response" }
          }
        }
      }'
