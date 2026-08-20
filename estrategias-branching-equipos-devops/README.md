# Estrategias de branching en Git: demo ejecutable

Ejemplo de código complementario al post [Estrategias de Branching en Git: Git Flow vs GitHub Flow vs GitLab Flow (2026)](https://www.devopsfreelance.pro/blog/posts/estrategias-branching-equipos-devops/).

## Qué demuestra este ejemplo

Dos scripts bash independientes que llevan a la práctica los conceptos centrales del post:

1. **`gitflow-demo.sh`**: crea un repositorio Git local (sin remoto) y ejecuta el ciclo completo de **Git Flow**: rama `develop`, una `feature/login-oauth` que se fusiona con `--no-ff`, una `release/1.1.0` que se cierra fusionando en `main` y `develop` con su tag, y un `hotfix/vulnerabilidad-sql` urgente que también se propaga a ambas ramas. Al final imprime el grafo de commits (`git log --all --graph --oneline`) para que veas exactamente la topología de ramas que genera Git Flow, la misma que describe el post.

2. **`validate-branch-name.sh`**: completa el script de validación de nombres de rama que el post deja esbozado en la sección "Caso 1: Empresa de software empresarial con releases trimestrales". Valida que un nombre de rama cumpla las convenciones de Git Flow / GitLab Flow (`feature/`, `release/<semver>`, `hotfix/`, `bugfix/`, ramas permanentes `main`/`develop`/`staging`/`production`, o releases estables estilo GitLab `N-N-stable`). Puede usarse como script de CLI suelto o instalarse como git hook (`pre-push`) para bloquear pushes con nombres de rama inconsistentes.

## Requisitos

- Git (cualquier versión reciente, probado con Git 2.x)
- Bash (probado con `bash` 5.x en Linux)
- No requiere Docker, red ni ningún servicio externo: todo corre en local con `git init` sobre un directorio temporal.

## Cómo correrlo

### 1. Demo completa de Git Flow

```bash
chmod +x gitflow-demo.sh
./gitflow-demo.sh
```

Esto crea un repo en un directorio temporal (`/tmp/gitflow-demo.XXXXXX`) y ejecuta feature → release → hotfix automáticamente. También podés indicar el directorio destino:

```bash
./gitflow-demo.sh /tmp/mi-demo-gitflow
cd /tmp/mi-demo-gitflow
git log --all --graph --oneline
```

**Salida esperada** (resumen, el hash de cada commit va a variar):

```
==> Repositorio de demo: /tmp/gitflow-demo.XXXXXX
==> Creando rama develop desde main
==> Feature branch: feature/login-oauth
==> Fusionando feature/login-oauth en develop (--no-ff)
==> Release branch: release/1.1.0
==> Cerrando release: merge en main y develop + tag
==> Hotfix urgente: hotfix/vulnerabilidad-sql
==> Cerrando hotfix: merge en main y develop + tag

==> Listo. Historial resultante:

*   7764bf9 (develop) Merge hotfix/vulnerabilidad-sql en develop
|\
* \   16641dd Merge release/1.1.0 en develop
...
* dec4390 Commit inicial en main

==> Ramas y tags creados:
  develop
* main
v1.1.0
v1.1.1
```

Al terminar quedan en el repo las ramas `main` y `develop`, y los tags `v1.1.0` y `v1.1.1`, tal como describe Git Flow en el post.

### 2. Validador de nombres de rama

```bash
chmod +x validate-branch-name.sh

# Valida un nombre puntual
./validate-branch-name.sh feature/login-oauth   # OK
./validate-branch-name.sh release/1.2.0         # OK
./validate-branch-name.sh cualquier-cosa        # ERROR, exit code 1

# Valida la rama actual del repo donde estés parado
./validate-branch-name.sh
```

**Salida esperada:**

```
$ ./validate-branch-name.sh feature/login-oauth
OK: 'feature/login-oauth' sigue la convencion feature/<identificador-en-minusculas-con-guiones>.

$ ./validate-branch-name.sh cualquier-cosa
ERROR: 'cualquier-cosa' no cumple ninguna convencion reconocida.
       Prefijos validos: feature/, release/, hotfix/, bugfix/
       Ramas permanentes validas: main, develop, staging, production
       Releases GitLab Flow: N-N-stable (ej: 2-3-stable)
```

Para instalarlo como hook y bloquear pushes de ramas mal nombradas en un repo real:

```bash
cp validate-branch-name.sh /ruta/a/tu/repo/.git/hooks/pre-push
chmod +x /ruta/a/tu/repo/.git/hooks/pre-push
```

## Notas

- Ningún script toca repositorios remotos ni requiere credenciales: ambos operan sobre git local.
- `gitflow-demo.sh` es idempotente en el sentido de que cada corrida crea un directorio nuevo (o el que le indiques); si le pasás un directorio existente con contenido, el `git init` fallará si ya hay commits en `main` con el mismo nombre de rama por defecto.
