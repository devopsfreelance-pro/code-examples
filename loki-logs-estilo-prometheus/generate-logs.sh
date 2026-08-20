#!/bin/sh
# Genera logs sinteticos y los envia a Loki via su API HTTP push,
# simulando lo que Promtail haria al recolectar logs de una app real.
set -eu

apk add --no-cache curl >/dev/null 2>&1

i=0
while true; do
  i=$((i + 1))
  if [ $((i % 5)) -eq 0 ]; then
    level=error
  else
    level=info
  fi
  ts=$(($(date +%s) * 1000000000))
  body="{\"streams\":[{\"stream\":{\"job\":\"demo-app\",\"level\":\"${level}\"},\"values\":[[\"${ts}\",\"{\\\"level\\\":\\\"${level}\\\",\\\"msg\\\":\\\"request procesado #${i}\\\",\\\"path\\\":\\\"/api/orders\\\"}\"]]}]}"
  curl -s -XPOST http://loki:3100/loki/api/v1/push \
    -H "Content-Type: application/json" \
    -d "${body}" >/dev/null
  sleep 2
done
