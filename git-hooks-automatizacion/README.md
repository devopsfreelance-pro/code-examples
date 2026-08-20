# Git Hooks: cliente + servidor de punta a punta

Ejemplo ejecutable del post: [Git Hooks: Guía Completa de Automatización DevOps 2026](https://www.devopsfreelance.pro/blog/posts/git-hooks-automatizacion/)

## Qué demuestra

El post describe hooks del lado del cliente (`pre-commit`, `commit-msg`) y del
lado del servidor (`post-receive`) como dos capas complementarias de
automatización. Este ejemplo arma el flujo completo en un entorno aislado:

- Un repo **bare** (`proyecto.git`) que simula el repositorio remoto, con un
  hook `post-receive` que hace checkout a un work-tree de "producción" y
  ejecuta un `deploy.sh` (el mismo patrón de despliegue automático del post,
  simplificado).
- Un repo **clonado** que simula la máquina del desarrollador, con dos hooks
  de cliente instalados:
  - `hooks/pre-commit`: bloquea commits que dejan líneas con espacios al
    final (falla de formato) o que introducen secretos hardcodeados
    (`api_key = "..."`, `password = "..."`, etc.), igual que el ejemplo de
    "Validación Avanzada de Código" del post.
  - `hooks/commit-msg`: exige Conventional Commits (`feat:`, `fix:`,
    `docs:`, etc.) y limita la primera línea a 72 caracteres, igual que el
    ejemplo de "Validación de Mensajes de Commit" del post.

`demo.sh` orquesta el ciclo completo: crea el repo bare con su hook,
clona, instala los hooks de cliente, hace un commit válido, lo pushea
(lo que dispara el deploy automático a "producción"), y después intenta
dos commits inválidos a propósito (uno con secreto, otro con mensaje mal
formado) para mostrar que los hooks los bloquean antes de que lleguen al
historial.

## Requisitos

- Git (cualquier versión reciente)
- Bash

No requiere Docker, Python ni ninguna dependencia externa. Todo corre en
directorios temporales bajo `/tmp`, sin tocar este repositorio.

## Cómo correrlo

```bash
cd git-hooks-automatizacion
chmod +x demo.sh hooks/pre-commit hooks/commit-msg hooks/post-receive
./demo.sh
```

El script crea su propio workspace con `mktemp -d`, así que se puede correr
las veces que haga falta sin dejar residuos. Al final imprime las rutas
(repo bare, repo de trabajo, directorio de "producción") por si se quiere
inspeccionar manualmente, junto con el comando para borrarlo.

## Salida esperada

```
== Workdir de la demo: /tmp/git-hooks-demo.XXXXXX ==

== 1) Creando repo bare (servidor) con hook post-receive ==
OK: repo bare creado en /tmp/git-hooks-demo.XXXXXX/proyecto.git

== 2) Clonando repo e instalando hooks de cliente ==
OK: hooks pre-commit y commit-msg instalados en .../desarrollador/.git/hooks

== 3) Commit inicial en main (debe pasar todas las validaciones) ==
Ejecutando validaciones pre-commit...
Todas las validaciones pre-commit pasaron exitosamente
Mensaje de commit válido (Conventional Commits)
OK: commit inicial creado

== 4) Push a main: dispara el post-receive y despliega a producción ==
  remote: Desplegando cambios a producción (rama: main)...
  remote: Ejecutando deploy.sh en producción...
  remote: Versión desplegada: <sha corto>
  remote: Servicio reiniciado (simulado)
  remote: Despliegue completado exitosamente

Contenido desplegado en producción:
  README.md
  deploy.sh

== 5) Pre-commit hook: intento de commitear un secreto (debe FALLAR) ==
Error: se detectó un posible secreto hardcodeado en el diff
OK: el hook bloqueó el commit con secreto hardcodeado, como se esperaba

== 6) Commit-msg hook: mensaje que no sigue Conventional Commits (debe FALLAR) ==
Error: el mensaje de commit no sigue el formato Conventional Commits
OK: el hook bloqueó el mensaje de commit inválido, como se esperaba
OK: reintentado con formato Conventional Commits, el commit pasó

== 7) Segundo push: nuevo deploy con la versión actualizada ==
  remote: Despliegue completado exitosamente

== Demo completa ==
Repo bare (servidor):  /tmp/git-hooks-demo.XXXXXX/proyecto.git
Repo de trabajo:       /tmp/git-hooks-demo.XXXXXX/desarrollador
Directorio producción: /tmp/git-hooks-demo.XXXXXX/producción

Para borrar todo: rm -rf /tmp/git-hooks-demo.XXXXXX
```

El exit code final es `0`. Si algún paso "que debe fallar" pasa
inesperadamente, el script corta con exit code `1` y lo marca como
`FALLO INESPERADO`.
