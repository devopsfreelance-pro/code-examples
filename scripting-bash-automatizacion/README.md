# Bash scripting confiable: modo estricto, trap, arrays y parameter expansion

Ejemplo de código para el post [Guía Definitiva de Bash Scripting para Automatización DevOps](https://www.devopsfreelance.pro/blog/posts/scripting-bash-automatizacion/).

## Qué demuestra

`deploy.sh` es un script de despliegue simulado que junta, en un solo archivo ejecutable,
las técnicas centrales del post:

- **Modo estricto** (`set -euo pipefail`): el script aborta ante cualquier comando que
  falle, en vez de seguir adelante sobre un estado inválido.
- **Cleanup garantizado con `trap ... EXIT`**: el directorio temporal de trabajo se borra
  siempre, haya éxito, error o interrupción (Ctrl+C).
- **Arrays en vez de strings separados por espacios**: la lista de servidores se recorre
  con `"${servers[@]}"` (comillas obligatorias).
- **Parameter expansion**:
  - `"${1:-staging}"` — valor por defecto si no se pasa argumento.
  - `"${API_TOKEN:?mensaje}"` — falla temprano con mensaje claro si falta una variable
    obligatoria.
  - `"${archivo%.tar.gz}"` — recorte de sufijo.
  - `"${API_TOKEN:0:3}"` — substring, para loguear un token sin exponerlo completo.
- **Manejo explícito de fallos aceptables**: `grep -c "ERROR" archivo || true`, para que
  un `grep` sin coincidencias no aborte el script bajo `pipefail`.

El script no toca servidores reales: "despliega" copiando un archivo simulado a
subdirectorios de un `mktemp -d`, así el ejemplo corre en minutos en cualquier máquina
con bash, sin infraestructura externa.

## Requisitos

- Bash 4+ (viene instalado en cualquier Linux o macOS moderno).
- Opcional: [ShellCheck](https://www.shellcheck.net/) para el linter (`sudo apt install
  shellcheck`, o vía Docker si no querés instalar nada: ver más abajo).

## Cómo correrlo

```bash
cd scripting-bash-automatizacion

# Dar permisos de ejecución (una sola vez)
chmod +x deploy.sh

# Ejecutar con entorno por defecto (staging) y un token de prueba
API_TOKEN=demo-token ./deploy.sh

# Ejecutar contra otro entorno
API_TOKEN=demo-token ./deploy.sh production
```

### Salida esperada

```
=== Despliegue a entorno: staging ===
Token API detectado (oculto): dem***
Nombre de artefacto: release-2026-08-20.tar.gz
Nombre sin extension: release-2026-08-20
  -> Desplegando en web01...
     Servicio myapp reiniciado en web01
  -> Desplegando en web02...
     Servicio myapp reiniciado en web02
  -> Desplegando en web03...
     Servicio myapp reiniciado en web03
Errores detectados en build: 0
=== Despliegue completado con exito en staging ===
Limpiando directorio temporal: /tmp/tmp.XXXXXXXXXX
```

(La fecha del artefacto y el nombre del directorio temporal van a variar en tu máquina.)

### Probar el modo estricto en acción

Si corrés el script sin definir `API_TOKEN`, la expansión `${API_TOKEN:?mensaje}` lo
corta de inmediato con un error claro, en vez de seguir hasta una llamada a una API con
un token vacío:

```bash
unset API_TOKEN
./deploy.sh staging
# ./deploy.sh: line 21: API_TOKEN: Definir API_TOKEN antes de ejecutar: export API_TOKEN=demo-token
```

### Correr ShellCheck (con o sin instalación local)

```bash
# Si tenés shellcheck instalado
shellcheck deploy.sh

# Sin instalar nada, vía Docker
docker run --rm -v "$PWD":/mnt koalaman/shellcheck:stable deploy.sh
```

El script pasa ShellCheck sin warnings: es el mismo criterio que aplica el post para
distinguir un script confiable de uno amateur.

## Notas

- No hay secretos reales involucrados: `API_TOKEN=demo-token` es un valor de ejemplo,
  no una credencial.
- El script no requiere red, Docker (salvo para ShellCheck opcional) ni permisos
  especiales: corre como usuario normal.
