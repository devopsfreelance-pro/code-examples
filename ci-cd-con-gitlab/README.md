# CI/CD con GitLab - ejemplo minimo

Post relacionado: [CI/CD GitLab: Automatización DevOps para Equipos Modernos](https://www.devopsfreelance.pro/blog/posts/ci-cd-con-gitlab/)

## Que demuestra este ejemplo

Un pipeline real de GitLab CI/CD (`.gitlab-ci.yml`) con las tres etapas que
describe el post: **build**, **test** y **deploy**, ejecutado de punta a
punta en tu maquina con Docker, sin necesidad de tener un servidor GitLab
propio ni una cuenta en GitLab.com.

El pipeline:

- **build**: valida que la app Python importe correctamente.
- **test**: instala `pytest` y corre la suite de tests, publicando un
  reporte JUnit como artifact (igual que lo haria un pipeline real contra
  un merge request).
- **deploy**: empaqueta la app en un `.tar.gz` versionado con el SHA del
  commit y simula un despliegue a staging con `echo` (sin credenciales ni
  infraestructura real). Solo corre automaticamente en `main`; en cualquier
  otra rama queda disponible como job manual, tal como recomienda el post
  para separar el pipeline de CI del gate de despliegue.

Ademas se usa `cache` (dependencias de `pip`) y `artifacts` con `needs`
entre etapas, que son los mecanismos que el post menciona para pasar
resultados entre jobs sin recompilar.

Para ejecutar `.gitlab-ci.yml` sin instalar GitLab se usa
[`gitlab-ci-local`](https://github.com/firecow/gitlab-ci-local), una
herramienta open source que interpreta el mismo archivo de configuracion y
corre cada job en un contenedor Docker, exactamente como lo haria un
GitLab Runner real.

Simplificacion a proposito: el `deploy` no publica a ningun destino real
(no hay servidor de staging en este repo), solo empaqueta el artifact y
loguea el paso. En un proyecto real ese `script` haria un `scp`, un
`kubectl apply` o un `aws s3 cp`, entre otros.

## Requisitos

- Docker (`docker --version`).
- Node.js >= 18 y `npx` (para correr `gitlab-ci-local` sin instalarlo
  globalmente).
- Conexion a internet la primera vez, para bajar la imagen `python:3.11-slim`
  y el paquete npm `gitlab-ci-local`.

## Pasos para correrlo

1. Pararte en este directorio:

   ```bash
   cd ci-cd-con-gitlab
   ```

2. Correr el pipeline completo (build, test y deploy) contra el
   `.gitlab-ci.yml` de este repo:

   ```bash
   npx --yes gitlab-ci-local@4.60.0
   ```

   La version se fija explicitamente (`@4.60.0`) porque las versiones mas
   nuevas de `gitlab-ci-local` requieren Node.js 22+; si ya tenes Node 22
   o superior podes omitir el `@4.60.0` y usar la ultima version.

3. Ver los artifacts generados (reporte de tests y el paquete de deploy):

   ```bash
   ls app/report.xml
   ls dist/
   ```

4. (Opcional) Correr un solo job, por ejemplo solo la etapa de test:

   ```bash
   npx --yes gitlab-ci-local@4.60.0 test
   ```

5. Limpiar los artifacts y la cache local generados por `gitlab-ci-local`:

   ```bash
   rm -rf .gitlab-ci-local dist app/report.xml app/__pycache__ app/.pytest_cache .cache
   ```

## Salida esperada

Al correr el paso 2 deberias ver, en orden, el job `build` importando
`app.py` sin errores, el job `test` con los 5 tests en verde:

```
test_app.py::test_descuento_veinte_por_ciento PASSED
test_app.py::test_descuento_cero_por_ciento PASSED
test_app.py::test_descuento_cien_por_ciento PASSED
test_app.py::test_precio_negativo_lanza_error PASSED
test_app.py::test_porcentaje_fuera_de_rango_lanza_error PASSED
```

y finalmente el job `deploy` generando `dist/app-<sha>.tar.gz` y logueando
`Deploy simulado -> entorno=staging paquete=dist/app-<sha>.tar.gz`, seguido
de:

```
 PASS  build
 PASS  test
 PASS  deploy
pipeline finished in ~20s
```

## Llevarlo a un GitLab real

Si queres ver este mismo `.gitlab-ci.yml` corriendo contra un GitLab Runner
de verdad: creá un proyecto vacio en GitLab.com (o en un GitLab
self-hosted), hacé push de este directorio como raiz del repo, y GitLab
detecta el `.gitlab-ci.yml` automaticamente. GitLab.com incluye runners
compartidos gratuitos para proyectos publicos y una cuota mensual gratuita
para privados, sin necesidad de registrar runner propio.
