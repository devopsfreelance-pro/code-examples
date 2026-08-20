#!/usr/bin/env bash
#
# demo.sh - Ejemplo ejecutable del post "Monorepo vs Multirepo".
#
# Crea un mini-monorepo temporal con 4 proyectos (api, web, docs, shared),
# hace un cambio en la librería compartida y usa affected.py (una versión
# minima de "nx affected") para mostrar como en un monorepo con grafo de
# dependencias solo se ejecutan tests/build de los proyectos afectados,
# en vez de todo el repositorio.
#
# No requiere Docker ni servicios externos: solo git y python3.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKDIR="$(mktemp -d /tmp/monorepo-demo.XXXXXX)"

cleanup() {
  rm -rf "${WORKDIR}"
}
trap cleanup EXIT

echo "== 1. Creando estructura de monorepo en ${WORKDIR} =="
mkdir -p "${WORKDIR}/apps/api" "${WORKDIR}/apps/web" "${WORKDIR}/apps/docs" "${WORKDIR}/libs/shared"

echo "print('api ok')"      > "${WORKDIR}/apps/api/main.py"
echo "console.log('web')"  > "${WORKDIR}/apps/web/index.js"
echo "# Docs del proyecto" > "${WORKDIR}/apps/docs/README.md"
echo "def helper(): return 1" > "${WORKDIR}/libs/shared/utils.py"

echo "== 2. Inicializando git y creando commit base =="
git -C "${WORKDIR}" init -q
git -C "${WORKDIR}" config user.email "demo@example.com"
git -C "${WORKDIR}" config user.name "demo"
git -C "${WORKDIR}" add -A
git -C "${WORKDIR}" commit -q -m "commit base: api, web, docs, shared"

echo "== 3. Modificando libs/shared (usada por api y web, no por docs) =="
echo "def helper(): return 2  # cambio de comportamiento" > "${WORKDIR}/libs/shared/utils.py"
git -C "${WORKDIR}" add -A
git -C "${WORKDIR}" commit -q -m "fix(shared): corrige valor de retorno de helper"

echo "== 4. Ejecutando affected.py contra el commit anterior (HEAD~1) =="
echo
python3 "${SCRIPT_DIR}/affected.py" \
  --repo "${WORKDIR}" \
  --base "HEAD~1" \
  --graph "${SCRIPT_DIR}/dependency-graph.json"

echo
echo "== Fin del demo. En un multirepo, este mismo cambio en 'shared' hubiera"
echo "requerido: publicar una nueva version del paquete, abrir un PR en el repo"
echo "de 'api' actualizando la dependencia, otro PR en 'web', y coordinar el"
echo "orden de despliegue. Aqui fue un unico commit y el pipeline detecto solo"
echo "los proyectos realmente afectados (docs se salteo)."
