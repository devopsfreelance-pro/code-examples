# Backstage.io Software Catalog: mini validador de entidades y relaciones

Ejemplo de código para el post del blog: [Guía Completa de Backstage.io para developer portals](https://www.devopsfreelance.pro/blog/posts/backstage-io-developer-portals/)

## Qué demuestra

El post explica que el corazón de Backstage es el **software catalog**: un conjunto de archivos `catalog-info.yaml` (entidades `Component`, `API`, `Resource`, `System`...) que describen los servicios de una organización, sus dueños y sus relaciones (`dependsOn`, `providesApis`), y que Backstage procesa automáticamente para generar el catálogo, detectar dependencias y alertar sobre relaciones rotas o servicios huérfanos.

`catalog_validator.py` reproduce esa misma lógica de ingesta y validación en un script standalone, sin necesidad de levantar el portal completo de Backstage (que requiere Node.js, una base de datos y varios minutos de setup):

- Carga todos los `catalog-info.yaml` de un directorio (`catalog/`), igual que el catalog-processor real.
- Indexa las entidades por referencia (`component:default/payment-service`), el mismo formato de refs que usa Backstage internamente.
- Valida que cada entidad tenga los campos obligatorios de su `kind` (`type`, `lifecycle`, `owner`).
- Valida que las relaciones `dependsOn` y `providesApis` apunten a entidades que realmente existen en el catálogo (en Backstage real esto dispara un "processing error" visible en la UI).
- Imprime el árbol de dependencias de cada `Component`, similar a la pestaña "Dependencies" de un servicio en el portal.

El directorio `catalog/` incluye el ejemplo `payment-service` / `user-service` tal cual aparece en el post, con una referencia rota a propósito (`payment-service` depende de `resource:default/payment-database`, que no está registrado) para mostrar cómo el validador la detecta.

## Requisitos

- Python 3.8 o superior
- PyYAML: `pip install pyyaml` (si no lo tenés instalado)

## Cómo correrlo

```bash
cd backstage-io-developer-portals

# Validar el catálogo tal como está (con la referencia rota a propósito)
python3 catalog_validator.py catalog
```

### Salida esperada (con el error intencional)

```
Software Catalog
========================================

API (2)
  - payment-api  (owner=team-payments)
  - user-api  (owner=team-identity)

Component (2)
  - payment-service  (owner=team-payments)
  - user-service  (owner=team-identity)

Resource (1)
  - user-database  (owner=team-identity)

Arbol de dependencias
========================================

payment-service
  -> component:default/user-service  [OK]
  -> resource:default/payment-database  [ROTA]

user-service
  -> resource:default/user-database  [OK]

Validacion
========================================
1 problema(s) encontrado(s):

  x [payment-service.yaml] 'payment-service' depende de 'resource:default/payment-database', pero esa entidad no existe en el catalogo
```

El script termina con código de salida `1` cuando hay errores (útil para usarlo como chequeo en un pipeline de CI que valide `catalog-info.yaml` antes de mergear).

### Para ver el caso "catálogo válido"

Agregá el `Resource` que falta a `catalog/resources.yaml` (o creá un archivo nuevo `catalog/payment-database.yaml`):

```yaml
apiVersion: backstage.io/v1alpha1
kind: Resource
metadata:
  name: payment-database
  description: Base de datos PostgreSQL de pagos
spec:
  type: database
  owner: team-payments
  system: e-commerce
```

Y volvé a correr `python3 catalog_validator.py catalog`: ahora la relación aparece `[OK]` y el script termina con "Catalogo valido" y código de salida `0`.

## Estructura

```
backstage-io-developer-portals/
├── catalog_validator.py       # el "catalog processor" mini
└── catalog/
    ├── payment-service.yaml   # Component (con dependsOn a user-service y payment-database)
    ├── user-service.yaml      # Component (con dependsOn a user-database)
    ├── apis.yaml               # API payment-api y user-api (multi-documento YAML)
    └── resources.yaml          # Resource user-database (payment-database falta a propósito)
```
