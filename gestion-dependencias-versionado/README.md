# Dependency Management: resolucion de versiones, conflictos y lockfiles

Ejemplo de código para el post [Dependency Management: Guía Completa para DevOps Modernos](https://www.devopsfreelance.pro/blog/posts/gestion-dependencias-versionado/).

## Qué demuestra

El post explica varios conceptos que suelen quedar en la teoría: rangos de
versión (`^`, `~`, exactas), resolución del grafo de dependencias,
"dependency hell" cuando dos paquetes exigen versiones incompatibles de una
tercera, y lockfiles como garantía de reproducibilidad.

Este ejemplo es un mini resolvedor de dependencias en Python puro (sin
librerías externas) que simula, a pequeña escala, lo que hace `npm install`,
`pip install` o `mvn install` por dentro:

1. **`semver_lib.py`**: parsea restricciones estilo `^1.2.3`, `~1.2.3`,
   `>=3.2,<4.0` o `==2.28.1` y calcula qué versiones las satisfacen, igual
   que interpreta npm o un `requirements.txt`.
2. **`resolve_dependencies.py`**: lee un manifiesto (`dependencies.json`),
   resuelve cada dependencia directa a la versión más alta compatible,
   recolecta las dependencias transitivas y detecta si dos paquetes piden
   rangos incompatibles de una misma librería compartida.
   - Con `dependencies.json` vas a ver un **conflicto real de versiones**
     (dependency hell): `auth-lib` necesita `http-client ^2.0.0` y
     `logging-lib` necesita `http-client ~1.4.0` al mismo tiempo. No existe
     una versión que cumpla ambas restricciones.
   - Con `dependencies-fixed.json` (mismo proyecto, `auth-lib` fijado a
     `~3.2.0` en vez de `^3.3.0`) la resolución es exitosa y el script
     escribe `lock.json` con las versiones exactas elegidas, tal como hace
     `package-lock.json` o `poetry.lock`.
3. Volver a correr el script contra `dependencies-fixed.json` genera un
   `lock.json` **idéntico** al anterior: esa es la garantía de
   reproducibilidad de la que habla el post.

`registry.json` simula el "registro de paquetes" (como npm o PyPI): declara
qué versiones existen de cada paquete y qué dependencias transitivas trae
cada una.

## Requisitos

- Python 3.9 o superior
- Sin dependencias externas (todo el ejemplo usa solo la librería estándar)

## Pasos para ejecutarlo

### 1. Ver un conflicto de versiones (dependency hell)

```bash
python3 resolve_dependencies.py dependencies.json
```

Salida esperada (código de salida `1`):

```
Resolviendo dependencias para 'checkout-service'...

  requiere directo: auth-lib ^3.3.0
  requiere directo: logging-lib ^1.0.0

RESOLUCION FALLIDA

  - CONFLICTO en 'http-client': auth-lib exige '^2.0.0', logging-lib exige '~1.4.0'. Ninguna version disponible (['1.4.0', '1.5.2', '2.0.0', '2.1.0']) satisface todas las restricciones simultaneamente. Esto es 'dependency hell'.

Asi se ve un conflicto real de versiones: ...
```

### 2. Resolver el conflicto y generar el lockfile

```bash
python3 resolve_dependencies.py dependencies-fixed.json --lockfile lock.json
cat lock.json
```

Salida esperada (código de salida `0`):

```
RESOLUCION EXITOSA

  auth-lib -> 3.2.0  (directa)
  http-client -> 1.4.0  (transitiva)
  logging-lib -> 1.2.0  (directa)

Lockfile escrito en 'lock.json'.
```

Y `lock.json`:

```json
{
  "project": "checkout-service",
  "resolved": {
    "auth-lib": "3.2.0",
    "http-client": "1.4.0",
    "logging-lib": "1.2.0"
  }
}
```

### 3. Comprobar la reproducibilidad del lockfile

```bash
cp lock.json lock_first_run.json
python3 resolve_dependencies.py dependencies-fixed.json --lockfile lock.json
diff lock_first_run.json lock.json && echo "IDENTICO -> reproducibilidad confirmada"
rm lock_first_run.json
```

El `diff` no muestra ninguna diferencia: dado el mismo manifiesto y el mismo
`registry.json`, el resolvedor siempre llega al mismo resultado exacto. En
un gestor de paquetes real esto es justamente lo que evita el "funciona en
mi máquina": el lockfile congela la resolución para que todos los entornos
instalen las mismas versiones.

## Ir más allá

- Editá `registry.json` y agregá una versión `2.1.0` de `logging-lib` cuya
  dependencia transitiva sea `http-client ^2.0.0`: vas a ver que
  `dependencies.json` (con `auth-lib ^3.3.0`) ahora sí resuelve sin
  conflicto, porque ambos paquetes convergen en el rango `2.x`.
- Cambiá la restricción de `auth-lib` en `dependencies-fixed.json` de
  `~3.2.0` a `^3.2.0`: el resolvedor vuelve a elegir `3.3.1` (la versión más
  alta que cumple el rango caret) y reaparece el conflicto, igual que
  describe el post sobre por qué `^` es "un arma de doble filo".
