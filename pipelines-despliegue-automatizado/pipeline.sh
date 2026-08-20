#!/usr/bin/env bash
# Simula un pipeline de despliegue automatizado con las fases descritas en el post:
# build -> test -> deploy (blue-green) -> verificacion -> rollback automatico si falla.
#
# Uso: ./pipeline.sh

set -euo pipefail

cd "$(dirname "$0")"

PROXY_URL="http://localhost:8080"
NEW_VERSION="green"
PREVIOUS_VERSION="blue"

log() {
    echo "[pipeline] $1"
}

stage_build() {
    log "Etapa BUILD: levantando contenedores de blue y green..."
    docker compose up -d app-blue app-green proxy
    log "Build OK."
}

stage_test() {
    log "Etapa TEST: verificando que ambos entornos responden..."
    sleep 2
    docker compose exec app-blue wget -q -O - http://localhost:5678 >/dev/null
    docker compose exec app-green wget -q -O - http://localhost:5678 >/dev/null
    log "Tests OK: blue y green responden correctamente."
}

stage_deploy() {
    log "Etapa DEPLOY: cambiando trafico de ${PREVIOUS_VERSION} a ${NEW_VERSION}..."
    ./switch-deployment.sh "${NEW_VERSION}"
}

stage_verify() {
    log "Etapa VERIFY: comprobando que el proxy sirve la nueva version..."
    sleep 1
    RESPONSE="$(curl -s "${PROXY_URL}")"
    log "Respuesta del proxy: ${RESPONSE}"

    if [[ "${RESPONSE}" != *"GREEN"* ]]; then
        log "Verificacion fallida. Ejecutando rollback automatico a ${PREVIOUS_VERSION}..."
        ./switch-deployment.sh "${PREVIOUS_VERSION}"
        exit 1
    fi

    log "Verificacion OK: green esta sirviendo trafico en produccion."
}

stage_build
stage_test
stage_deploy
stage_verify

log "Pipeline completado con exito. Version desplegada: ${NEW_VERSION}."
