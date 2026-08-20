# Pipeline de despliegue automatizado con blue-green (mini ejemplo)

Post: [Pipelines de Despliegue Automatizado: Guía Completa 2026](https://www.devopsfreelance.pro/blog/posts/pipelines-despliegue-automatizado/)

## Qué demuestra

Este ejemplo reproduce en miniatura el flujo descrito en el post: un pipeline
que pasa por las etapas **build -> test -> deploy -> verify**, y usa una
estrategia de **despliegue blue-green** para pasar tráfico de una versión
(`blue`) a la siguiente (`green`) sin downtime, con **rollback automático**
si la verificación post-despliegue falla.

Componentes:

- `app-blue` / `app-green`: dos "versiones" de una app (contenedores
  `hashicorp/http-echo`, cada uno responde un texto distinto para poder
  distinguir a cuál está apuntando el tráfico).
- `proxy` (nginx): enruta el tráfico real hacia la versión activa. Es el
  equivalente al load balancer / router que en producción se reconfigura
  para el switch blue-green.
- `switch-deployment.sh`: cambia el upstream activo del proxy (blue <->
  green) y recarga nginx sin cortar conexiones.
- `pipeline.sh`: orquesta las etapas del pipeline (equivalente a un job de
  GitLab CI / GitHub Actions), incluyendo la verificación post-despliegue y
  el rollback automático si algo falla.

## Requisitos

- Docker con Docker Compose v2 (`docker compose version`)
- `curl`

No requiere cuentas en la nube ni servicios pagos: todo corre localmente.

## Cómo correrlo

```bash
cd pipelines-despliegue-automatizado

# Dar permisos de ejecución a los scripts
chmod +x pipeline.sh switch-deployment.sh

# Ejecutar el pipeline completo: build, test, deploy (blue -> green), verify
./pipeline.sh
```

### Salida esperada

```
[pipeline] Etapa BUILD: levantando contenedores de blue y green...
[pipeline] Build OK.
[pipeline] Etapa TEST: verificando que ambos entornos responden...
[pipeline] Tests OK: blue y green responden correctamente.
[pipeline] Etapa DEPLOY: cambiando trafico de blue a green...
Trafico redirigido a app-green.
[pipeline] Etapa VERIFY: comprobando que el proxy sirve la nueva version...
[pipeline] Respuesta del proxy: Respuesta desde GREEN (v2.0)
[pipeline] Verificacion OK: green esta sirviendo trafico en produccion.
[pipeline] Pipeline completado con exito. Version desplegada: green.
```

### Probar el switch manualmente

```bash
# Ver a qué versión está apuntando el proxy ahora mismo
curl http://localhost:8080

# Volver a blue (simula un rollback manual)
./switch-deployment.sh blue
curl http://localhost:8080
```

### Simular un fallo y ver el rollback automático

Editá `pipeline.sh` y cambiá la condición de `stage_verify` para que espere
un texto que nunca va a aparecer (por ejemplo `"NO-EXISTE"` en vez de
`"GREEN"`), volvé a correr `./pipeline.sh` y vas a ver que el pipeline
detecta la falla y ejecuta `switch-deployment.sh blue` automáticamente antes
de salir con código de error 1.

### Limpiar

```bash
docker compose down
```

## Relación con el post

- La fase `stage_build` / `stage_test` de `pipeline.sh` es la versión
  ejecutable del bloque YAML conceptual de compilación del post.
- `switch-deployment.sh` implementa la estrategia **blue-green** descrita en
  "Estrategias de Despliegue Progresivo": dos entornos idénticos y un cambio
  de tráfico instantáneo.
- `stage_verify` con rollback automático ilustra el punto del post sobre
  detectar anomalías post-despliegue y revertir sin intervención humana.
