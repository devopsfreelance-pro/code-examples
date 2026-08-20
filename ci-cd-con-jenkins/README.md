# CI/CD con Jenkins - ejemplo minimo

Post relacionado: [Guía Completa de Ci/cd con jenkins](https://www.devopsfreelance.pro/blog/posts/ci-cd-con-jenkins/)

## Que demuestra este ejemplo

Un Jenkins controller corriendo en Docker, con un `Jenkinsfile` declarativo real
que ejecuta las etapas centrales que describe el post: checkout, install,
test y build, con un bloque `post` que reporta el resultado. El objetivo es
que puedas ver un pipeline de Jenkins como código corriendo de punta a punta
en tu maquina, sin depender de un servidor externo ni de un registry.

Simplificaciones a proposito, documentadas para que no generen confusion:

- El pipeline usa `agent any`, es decir corre en el controller. El post
  explica por que en producción esto no es recomendable (seguridad, recursos);
  aca se hace asi porque es un demo de un solo contenedor sin agents
  adicionales.
- La app de ejemplo (`app/`) es un modulo Node.js sin dependencias, para que
  `npm install` y `npm test` corran en segundos sin bajar nada de internet
  mas que el propio Node.
- El stage "Build" empaqueta la app en un `.tar.gz` en vez de construir y
  publicar una imagen Docker, para no depender de un registry ni de montar
  el socket de Docker dentro del contenedor de Jenkins.

## Requisitos

- Docker y Docker Compose v2 (`docker compose version`).
- Puertos `8080` y `50000` libres en tu maquina.
- ~2 GB de RAM libres para el contenedor de Jenkins.

## Pasos para correrlo

1. Pararte en este directorio:

   ```bash
   cd ci-cd-con-jenkins
   ```

2. Construir y levantar Jenkins (la primera vez tarda unos minutos porque
   instala Node.js y los plugins de Jenkins dentro de la imagen):

   ```bash
   docker compose up -d --build
   ```

3. Esperar a que Jenkins este listo y obtener la contraseña inicial de admin:

   ```bash
   docker compose logs -f jenkins
   # Esperar el mensaje "Jenkins is fully up and running", luego Ctrl+C

   docker compose exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
   ```

4. Abrir <http://localhost:8080> en el navegador, pegar la contraseña del
   paso anterior y en la pantalla de "Customize Jenkins" elegir
   **"Skip and continue as admin"** (los plugins necesarios ya vienen
   instalados en la imagen, no hace falta el wizard de "Install suggested
   plugins").

5. Crear el pipeline: en el dashboard, click en **"New Item"**, nombre
   `hello-ci-cd`, tipo **Pipeline**, click **OK**.

6. En la configuración del job, bajar hasta la sección **Pipeline**:
   - **Definition:** `Pipeline script`
   - **Script:** pegar el contenido completo del archivo [`Jenkinsfile`](./Jenkinsfile) de este directorio.
   - Guardar (**Save**).

7. Click en **"Build Now"** (en el menu lateral del job).

8. Click en el build `#1` y despues en **"Console Output"** para ver el
   log completo.

## Salida esperada

En el console output del build vas a ver, entre otras lineas:

```
[Pipeline] { (Test)
+ npm test
> node -e "const {sum}=require('./index'); ..."
OK: sum(2,3) === 5
[Pipeline] { (Build)
+ tar -czf ../hello-ci-cd-1.tar.gz .
+ ls -la hello-ci-cd-1.tar.gz
-rw-r--r-- 1 jenkins jenkins  ... hello-ci-cd-1.tar.gz
Build OK: hello-ci-cd #1
Finished: SUCCESS
```

## Limpiar

```bash
docker compose down -v
```

Esto borra tambien el volumen `jenkins_home` (configuración y builds de
Jenkins guardados durante la prueba).
