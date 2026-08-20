# Node.js DevOps: npm scripts, health check y validación de configuración

Ejemplo de código que acompaña al post [Node.js DevOps: Automatización moderna con JavaScript](https://www.devopsfreelance.pro/blog/posts/javascript-node-js-devops/).

## Qué demuestra

El post explica cómo Node.js reemplaza a Bash/Python en tareas típicas de DevOps
gracias a su modelo asíncrono no bloqueante y a npm scripts como capa de
orquestación. Este ejemplo reproduce en miniatura los dos scripts que aparecen
en el post:

- **`scripts/health-check.js`**: health check HTTP asíncrono con el módulo
  nativo `http` (sin dependencias), con timeout y códigos de salida
  compatibles con CI/CD (`exit 0` sano, `exit 1` degradado o inalcanzable).
- **`scripts/validate-infrastructure.js`**: valida un archivo de
  configuración (`infra-config.json`) antes de un despliegue, usando
  `fs/promises` y sin librerías externas.
- **`package.json`**: los `npm scripts` que orquestan todo (`stack:up`,
  `health`, `infra:validate`), tal como recomienda el post en vez de usar
  Grunt/Gulp para tareas simples.

## Requisitos

- Node.js 18+ (usa `fs/promises`, disponible desde Node 14+, pero se recomienda 18 LTS o superior)
- Docker y Docker Compose (para levantar el servicio de prueba contra el que corre el health check)

No hace falta `npm install`: todo el ejemplo usa módulos nativos de Node.js.

## Pasos para correrlo

1. Levantar un servicio de prueba (nginx local, simula "myapp" del post):

```bash
npm run stack:up
```

2. Correr el health check asíncrono contra ese servicio:

```bash
npm run health
```

Salida esperada:

```
Servicio saludable (HTTP 200) - http://localhost:8080/
```

El comando termina con código de salida `0`. Podés probar el caso de fallo
apagando el stack (`npm run stack:down`) y corriendo `npm run health` de
nuevo: va a fallar con `ECONNREFUSED` y código de salida `1`, el mismo
comportamiento que usaría un pipeline de CI/CD para bloquear un despliegue.

3. Validar la configuración de infraestructura antes de un despliegue:

```bash
npm run infra:validate
```

Salida esperada:

```
Validando configuracion: .../infra-config.json
Configuracion valida:
  servicio:    myapp
  entorno:     staging
  replicas:    3
  imagen:      myapp:latest
```

Para ver el caso de error, editá `infra-config.json` y poné, por ejemplo,
`"environment": "qa"` o `"replicas": 0`, y volvé a correr el comando: el
script va a listar los errores y salir con código `1`.

4. Apagar el stack de prueba:

```bash
npm run stack:down
```

## Estructura

```
javascript-node-js-devops/
├── package.json                    # npm scripts de orquestación
├── docker-compose.yml              # servicio de prueba (nginx) para el health check
├── infra-config.json               # configuración de ejemplo a validar
├── scripts/
│   ├── health-check.js             # health check HTTP asíncrono
│   └── validate-infrastructure.js  # validación de configuración pre-despliegue
└── README.md
```
