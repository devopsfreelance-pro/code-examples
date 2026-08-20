#!/bin/bash
#
# deploy.sh - Demo de un script de despliegue "confiable" en Bash.
#
# Combina, en un solo script ejecutable, las técnicas centrales del post:
#   - modo estricto: set -euo pipefail
#   - cleanup garantizado con trap ... EXIT
#   - arrays en vez de strings separados por espacios
#   - parameter expansion (valor por defecto, variable obligatoria, recorte de sufijo)
#   - manejo explícito de comandos que pueden fallar sin abortar el script (|| true)
#
# No toca servidores reales: "despliega" copiando archivos a un directorio
# temporal, para que el ejemplo corra en minutos en cualquier máquina con bash.

set -euo pipefail

# Parameter expansion: valor por defecto si no se pasó argumento.
ENVIRONMENT="${1:-staging}"

# Parameter expansion: falla temprano y con mensaje claro si falta la variable.
API_TOKEN="${API_TOKEN:?Definir API_TOKEN antes de ejecutar: export API_TOKEN=demo-token}"

# Directorio de trabajo temporal + cleanup garantizado.
WORKDIR=$(mktemp -d)

cleanup() {
    echo "Limpiando directorio temporal: $WORKDIR"
    rm -rf "$WORKDIR"
}
trap cleanup EXIT

# Array de "servidores" a los que se despliega. Las comillas en "${servers[@]}"
# son obligatorias: sin ellas, un nombre con espacio se partiría en dos elementos.
servers=("web01" "web02" "web03")

deploy_to_server() {
    local server="$1"
    echo "  -> Desplegando en ${server}..."
    mkdir -p "$WORKDIR/$server"
    cp "$WORKDIR/build/app.txt" "$WORKDIR/$server/app.txt"
    echo "     Servicio myapp reiniciado en ${server}"
}

echo "=== Despliegue a entorno: $ENVIRONMENT ==="
echo "Token API detectado (oculto): ${API_TOKEN:0:3}***"

mkdir -p "$WORKDIR/build"

# Parameter expansion: recorte de sufijo/prefijo, igual que en el post.
archivo="release-$(date +%Y-%m-%d).tar.gz"
echo "contenido simulado del build" > "$WORKDIR/build/app.txt"
echo "Nombre de artefacto: $archivo"
echo "Nombre sin extension: ${archivo%.tar.gz}"

for server in "${servers[@]}"; do
    deploy_to_server "$server"
done

# grep sin coincidencias devuelve 1 y con pipefail activo abortaría el script;
# "|| true" documenta que ese fallo puntual es aceptable y esperado.
failed_checks=$(grep -c "ERROR" "$WORKDIR/build/app.txt" || true)
echo "Errores detectados en build: $failed_checks"

echo "=== Despliegue completado con exito en $ENVIRONMENT ==="
