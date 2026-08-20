# Monorepo vs Multirepo: demo de "affected projects"

Ejemplo de código para el post [Monorepo vs Multirepo: Guía completa para equipos DevOps](https://www.devopsfreelance.pro/blog/posts/gestion-repositorios-monorepo-vs-multirepo/).

## Qué demuestra

El post explica que una de las ventajas técnicas centrales del monorepo (frente
al multirepo) es poder ejecutar CI/CD **solo sobre los proyectos afectados**
por un cambio, en vez de sobre todo el repositorio, usando un grafo de
dependencias (`nx affected`, `turbo run --filter`, etc.).

Este ejemplo reimplementa esa idea en ~100 líneas de Python (`affected.py`):

1. Crea un mini-monorepo con 4 proyectos: `apps/api`, `apps/web`, `apps/docs`
   y `libs/shared` (`api` y `web` dependen de `shared`; `docs` es independiente).
2. Modifica `libs/shared` en un commit.
3. Compara ese commit contra el anterior con `git diff`, cruza los archivos
   modificados contra `dependency-graph.json` y calcula qué proyectos están
   afectados **directamente** y por **dependencia transitiva**.
4. Simula la ejecución de test/build solo para los proyectos afectados
   (`api`, `web`, `shared`) y muestra que `docs` se salta, ahorrando tiempo
   de CI, exactamente el comportamiento que describe el post para Nx.

También sirve para visualizar el contraste con multirepo: el mismo cambio en
`shared`, si viviera en un repositorio aparte, habría requerido publicar una
versión nueva del paquete y abrir un PR en cada repo consumidor (`api`, `web`)
para actualizar la dependencia, tal como se explica en la sección "Gestión de
Multirepo" del post.

## Requisitos

- `git` (cualquier versión reciente)
- `python3` (3.9 o superior, sin dependencias externas)
- Bash (Linux/macOS/WSL)

No hace falta Docker, Node ni instalar Nx: el script simula el comportamiento
de "affected" con las herramientas estándar del sistema.

## Cómo ejecutarlo

```bash
cd gestion-repositorios-monorepo-vs-multirepo
chmod +x demo.sh affected.py
./demo.sh
```

El script crea el monorepo de prueba en un directorio temporal (`mktemp -d`)
y lo borra automáticamente al terminar. No modifica nada fuera de `/tmp`.

### Ejecutar `affected.py` manualmente contra otro escenario

```bash
python3 affected.py \
  --repo /ruta/a/tu/repo \
  --base HEAD~1 \
  --graph dependency-graph.json
```

Ajustá `dependency-graph.json` con las rutas y dependencias reales de tu
propio monorepo para probar el mismo cálculo de "afectados" sobre tu código.

## Salida esperada

```
== 1. Creando estructura de monorepo en /tmp/monorepo-demo.XXXXXX ==
== 2. Inicializando git y creando commit base ==
== 3. Modificando libs/shared (usada por api y web, no por docs) ==
== 4. Ejecutando affected.py contra el commit anterior (HEAD~1) ==

Archivos modificados desde HEAD~1:
  - libs/shared/utils.py

Proyectos tocados directamente: ['shared']
Proyectos afectados (directos + dependientes): ['api', 'shared', 'web']
Proyectos NO afectados (se saltan build/test): ['docs']

Ejecutando pipeline solo sobre proyectos afectados:
  -> nx run api:test   [OK] (simulado)
  -> nx run api:build  [OK] (simulado)
  -> nx run shared:test   [OK] (simulado)
  -> nx run shared:build  [OK] (simulado)
  -> nx run web:test   [OK] (simulado)
  -> nx run web:build  [OK] (simulado)

Proyectos saltados (sin cambios relevantes, ahorran tiempo de CI):
  -> docs: skip

== Fin del demo. En un multirepo, este mismo cambio en 'shared' hubiera
requerido: publicar una nueva version del paquete, abrir un PR en el repo
de 'api' actualizando la dependencia, otro PR en 'web', y coordinar el
orden de despliegue. Aqui fue un unico commit y el pipeline detecto solo
los proyectos realmente afectados (docs se salteo).
```

## Archivos

- `demo.sh` - orquesta el escenario completo (setup, commit, cambio, ejecución).
- `affected.py` - lógica de cálculo de proyectos afectados a partir de
  `git diff` y el grafo de dependencias.
- `dependency-graph.json` - grafo de dependencias de ejemplo (equivalente
  simplificado al `project.json` + `nx.json` de un workspace Nx real).
