# Git hooks + Trunk-Based Development

Ejemplo ejecutable del post: [Git Workflow: Estrategias Avanzadas para Equipos DevOps](https://www.devopsfreelance.pro/blog/posts/git-avanzado-equipos-devops/)

## Qué demuestra

El post describe tres pilares de un git workflow avanzado: branching (Trunk-Based
Development), automatización con hooks (client-side y server-side) y gestión de
dependencias con submodules. Este ejemplo se enfoca en el pilar más fácil de
ejecutar y verificar en minutos: **hooks de Git aplicando reglas del equipo**,
combinado con un ciclo corto de **Trunk-Based Development**.

`demo.sh` crea un repositorio Git temporal (en `/tmp`, no toca este repo) e instala
dos hooks:

- `hooks/pre-commit`: bloquea commits que contienen credenciales hardcodeadas
  (`api_key = "..."`, `password = "..."`, etc.) o archivos de más de 1MB (que
  deberían versionarse con Git LFS en vez de ir directo al historial).
- `hooks/commit-msg`: bloquea commits cuyo mensaje no sigue Conventional Commits
  (`feat: `, `fix: `, `chore: `, etc.), simulando la misma validación que en el
  post se aplica del lado del servidor con `pre-receive`.

Luego el script recorre un ciclo típico de Trunk-Based Development: crea una rama
`feature/add-app` de corta duración, commitea, y la integra a `main` con
`git merge --no-ff`, dejando el árbol listo para inspeccionar con `git log --graph`.

## Requisitos

- Git (cualquier versión reciente)
- Bash

No requiere Docker, Python ni ninguna dependencia externa.

## Cómo correrlo

```bash
cd git-avanzado-equipos-devops
chmod +x demo.sh hooks/pre-commit hooks/commit-msg
./demo.sh
```

El script crea su propio repo temporal (`mktemp -d`), así que se puede correr las
veces que haga falta sin dejar residuos en este repositorio. Al final imprime la
ruta del repo temporal por si se quiere inspeccionar manualmente, con el comando
para borrarlo.

## Salida esperada

```
== Repo de demo en: /tmp/git-avanzado-demo.XXXXXX ==

== 1) Commit inicial en main ==
Ejecutando validaciones pre-commit...
Todas las validaciones pre-commit pasaron
Mensaje de commit válido (Conventional Commits)
OK: commit inicial creado

== 2) Pre-commit hook: intento de commitear una credencial (debe FALLAR) ==
OK: el hook bloqueó el commit con credencial hardcodeada, como se esperaba
...
ERROR: posibles credenciales detectadas en el código staged

== 3) Commit-msg hook: mensaje que NO sigue Conventional Commits (debe FALLAR) ==
OK: el hook bloqueó el mensaje que no sigue Conventional Commits
...
ERROR: el mensaje de commit no sigue Conventional Commits

== 4) Commit válido siguiendo Trunk-Based Development ==
OK: commit válido en rama de feature de corta duración
OK: merge a main y rama de feature eliminada (ciclo cerrado en minutos)

== Historial final ==
*   d44b577 chore: merge feature/add-app into main
|\
| * 136d1ba feat(app): add hello world script
|/
* edb2127 chore: commit inicial

== Demo completa. Repo temporal: /tmp/git-avanzado-demo.XXXXXX ...
```

Los hashes de commit van a variar en cada corrida; lo relevante es que los pasos 2
y 3 fallan como se espera (el hook bloquea) y el paso 4 completa el merge sin
intervención manual.

## Cómo instalar estos hooks en un repo real

```bash
cp hooks/pre-commit .git/hooks/pre-commit
cp hooks/commit-msg .git/hooks/commit-msg
chmod +x .git/hooks/pre-commit .git/hooks/commit-msg
```

Para distribuirlos entre el equipo sin depender de una copia manual, usar
[pre-commit framework](https://pre-commit.com/) (Python) o [Husky](https://typicode.github.io/husky/)
(JavaScript), como se menciona en el post.

## Notas

- No hay credenciales ni cuentas externas involucradas: `sk-1234567890abcdef` en el
  paso 2 es un valor de ejemplo dentro del propio repo temporal de la demo, nunca
  se envía a ningún lado.
- El ejemplo no cubre submodules porque requeriría un segundo repositorio remoto
  real para ilustrarse con fidelidad; los comandos relevantes ya están documentados
  en el post (`git submodule update --init --recursive`, `--remote --merge`).
