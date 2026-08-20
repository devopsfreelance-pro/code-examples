# Políticas de Seguridad como Código: Conftest en modo audit vs enforce

Post relacionado: [Políticas de Seguridad como Código: Guía Completa de Policy as Code](https://www.devopsfreelance.pro/blog/posts/implementacion-politicas-seguridad-codigo/)

## Qué demuestra este ejemplo

El post explica que Conftest empaqueta OPA para CI/CD ("evalúa archivos de
configuración contra políticas Rego y falla con exit code distinto de cero
si algo viola las reglas") y que la implementación gradual pasa por dos
etapas: primero **modo audit** (la política reporta violaciones pero no
bloquea) y después **modo enforce** (la política bloquea el pipeline).

Este ejemplo reproduce exactamente esas dos etapas con la política Rego del
post (bucket S3 con ACLs públicas) usando Conftest 100% en local vía Docker,
sin necesitar Terraform instalado ni una cuenta de AWS:

1. `policy/terraform/s3.rego` tiene dos reglas:
   - `deny`: la regla de **enforce** del post (bucket con
     `block_public_acls == false`), la misma que aparece en el artículo.
   - `warn`: una regla en **modo audit** (bucket sin cifrado configurado)
     que reporta la violación sin hacer fallar el pipeline, ilustrando el
     paso 2 de la "Implementación gradual" del post.
2. `examples/plan-no-conforme.json` y `examples/plan-conforme.json` simulan
   la salida de `terraform show -json` para un bucket público y sin cifrar,
   y para uno privado y cifrado, respectivamente.
3. `run.sh` corre Conftest contra cada plan y muestra cómo cambia el exit
   code: `1` cuando hay una violación de tipo `deny` (bloquea el merge),
   `0` cuando solo hay `warn` o cuando el recurso cumple.

## Requisitos

- Docker (para correr Conftest sin instalarlo localmente)
- Nada más: no hace falta Terraform, ni AWS, ni Kubernetes

## Cómo correrlo

```bash
cd implementacion-politicas-seguridad-codigo
./run.sh
```

También se puede correr un solo caso:

```bash
./run.sh no-conforme   # bucket publico y sin cifrar
./run.sh conforme      # bucket privado y cifrado
```

Internamente, cada corrida usa Conftest así (igual que el job de GitHub
Actions del post, pero apuntando al plan de ejemplo en vez de a un
`terraform plan` real):

```bash
docker run --rm -v "$(pwd):/project" -w /project \
  openpolicyagent/conftest:v0.56.0 \
  test examples/plan-no-conforme.json --policy policy/terraform --all-namespaces
```

## Salida esperada

Con `plan-no-conforme.json` (bucket público y sin cifrar):

```
+---------+--------------------------------+--------------+----------------------------------------+
| RESULT  |              FILE              |  NAMESPACE   |                MESSAGE                 |
+---------+--------------------------------+--------------+----------------------------------------+
| warning | examples/plan-no-conforme.json | terraform.s3 | El bucket aws_s3_bucket.logs no tiene  |
|         |                                |              | cifrado en reposo configurado (regla   |
|         |                                |              | en modo audit, no bloquea)             |
| failure | examples/plan-no-conforme.json | terraform.s3 | El bucket aws_s3_bucket_public_access_ |
|         |                                |              | block.logs permite ACLs publicas:      |
|         |                                |              | bloqueado por politica de seguridad    |
+---------+--------------------------------+--------------+----------------------------------------+
exit code deny: 1
```

Con `plan-conforme.json` (bucket privado y cifrado), ambas reglas pasan y
el exit code es `0`:

```
+---------+-----------------------------+--------------+---------+
| RESULT  |            FILE             |  NAMESPACE   | MESSAGE |
+---------+-----------------------------+--------------+---------+
| success | examples/plan-conforme.json | terraform.s3 | SUCCESS |
| success | examples/plan-conforme.json | terraform.s3 | SUCCESS |
+---------+-----------------------------+--------------+---------+
exit code deny: 0
```

Esto es lo que en un pipeline real determina si el job `policy-check` deja
pasar el merge (`plan-conforme.json`) o lo bloquea (`plan-no-conforme.json`),
tal como describe la sección "Integración en el pipeline" del post.

## Estructura

```
implementacion-politicas-seguridad-codigo/
├── README.md
├── run.sh                          # orquesta las corridas audit/enforce
├── policy/
│   └── terraform/
│       └── s3.rego                 # reglas deny (enforce) y warn (audit)
└── examples/
    ├── plan-no-conforme.json       # bucket publico y sin cifrar
    └── plan-conforme.json          # bucket privado y cifrado
```
