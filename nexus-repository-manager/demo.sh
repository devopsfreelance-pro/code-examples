#!/usr/bin/env bash
# Demuestra los tres tipos de repositorio de Nexus (proxy, hosted, group)
# descritos en el post, contra una instancia real levantada con docker-compose.
set -euo pipefail

NEXUS_URL="http://localhost:8081"
ADMIN_PASSWORD_FILE_IN_CONTAINER="/nexus-data/admin.password"
CONTAINER_NAME="nexus-demo"

echo "==> 1) Esperando a que Nexus responda en ${NEXUS_URL} ..."
until curl -s -o /dev/null -w "%{http_code}" "${NEXUS_URL}/service/rest/v1/status" | grep -q "200"; do
  printf "."
  sleep 5
done
echo
echo "Nexus está arriba."

echo "==> 2) Obteniendo password inicial de admin ..."
ADMIN_PASSWORD=$(docker exec "${CONTAINER_NAME}" cat "${ADMIN_PASSWORD_FILE_IN_CONTAINER}")
echo "Password inicial obtenida (se usa solo para esta demo local)."

AUTH=(-u "admin:${ADMIN_PASSWORD}")

echo
echo "==> 3) Repositorio PROXY: maven-central ya viene creado por defecto en Nexus OSS."
echo "    Descargamos la misma dependencia dos veces a través del proxy y medimos el tiempo."
echo "    La primera vez Nexus la baja de Maven Central; la segunda la sirve desde su caché local."

ARTIFACT_PATH="org/apache/commons/commons-lang3/3.14.0/commons-lang3-3.14.0.jar"
PROXY_URL="${NEXUS_URL}/repository/maven-central/${ARTIFACT_PATH}"

echo
echo "--- Descarga 1 (origen remoto) ---"
START1=$(date +%s%N)
curl -s -o /tmp/commons-lang3-1.jar "${PROXY_URL}"
END1=$(date +%s%N)
MS1=$(( (END1 - START1) / 1000000 ))
echo "Tiempo: ${MS1} ms | tamaño: $(stat -c%s /tmp/commons-lang3-1.jar 2>/dev/null || stat -f%z /tmp/commons-lang3-1.jar) bytes"

echo
echo "--- Descarga 2 (desde caché de Nexus) ---"
START2=$(date +%s%N)
curl -s -o /tmp/commons-lang3-2.jar "${PROXY_URL}"
END2=$(date +%s%N)
MS2=$(( (END2 - START2) / 1000000 ))
echo "Tiempo: ${MS2} ms | tamaño: $(stat -c%s /tmp/commons-lang3-2.jar 2>/dev/null || stat -f%z /tmp/commons-lang3-2.jar) bytes"
echo
echo "La descarga cacheada (2) debería ser notablemente más rápida que la original (1)."

echo
echo "==> 4) Repositorio HOSTED: creamos uno raw para artefactos propios y publicamos uno."
curl -s "${AUTH[@]}" -X POST "${NEXUS_URL}/service/rest/v1/repositories/raw/hosted" \
  -H "Content-Type: application/json" \
  -d '{
        "name": "internal-artifacts",
        "online": true,
        "storage": {
          "blobStoreName": "default",
          "strictContentTypeValidation": true,
          "writePolicy": "ALLOW"
        },
        "raw": {
          "contentDisposition": "ATTACHMENT"
        }
      }' > /dev/null || echo "(el repositorio 'internal-artifacts' ya existía, seguimos)"

echo "hola desde devopsfreelance.pro - $(date -u +%FT%TZ)" > /tmp/mi-artefacto.txt

echo "--- Publicando /tmp/mi-artefacto.txt en el repo hosted ---"
curl -s "${AUTH[@]}" -X PUT \
  "${NEXUS_URL}/repository/internal-artifacts/demo/mi-artefacto.txt" \
  --upload-file /tmp/mi-artefacto.txt

echo "--- Descargando de vuelta el mismo artefacto ---"
curl -s "${AUTH[@]}" "${NEXUS_URL}/repository/internal-artifacts/demo/mi-artefacto.txt"

echo
echo "==> 5) Repositorio GROUP: unificamos el proxy y el hosted bajo una sola URL."
curl -s "${AUTH[@]}" -X POST "${NEXUS_URL}/service/rest/v1/repositories/raw/group" \
  -H "Content-Type: application/json" \
  -d '{
        "name": "todo-en-uno",
        "online": true,
        "storage": {
          "blobStoreName": "default",
          "strictContentTypeValidation": true
        },
        "group": {
          "memberNames": ["internal-artifacts"]
        }
      }' > /dev/null || echo "(el repositorio 'todo-en-uno' ya existía, seguimos)"

echo "--- Listando repositorios existentes en esta instancia ---"
curl -s "${AUTH[@]}" "${NEXUS_URL}/service/rest/v1/repositories" \
  | python3 -c "import json,sys; [print(f\"  {r['type']:8s} {r['format']:6s} {r['name']}\") for r in json.load(sys.stdin)]"

echo
echo "Demo completa. UI disponible en ${NEXUS_URL} (usuario admin, password: ${ADMIN_PASSWORD})"
