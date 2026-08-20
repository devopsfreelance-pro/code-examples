# Shift Left Testing en DevOps: ejemplo ejecutable

Post: [Shift Left: Guía completa para testing temprano en DevOps](https://www.devopsfreelance.pro/blog/posts/shift-left-testing-devops/)

## Qué demuestra este ejemplo

El post describe la pirámide de testing y el "test driven infrastructure" en
teoría. Este directorio lo hace tangible con dos de los pilares que menciona
el artículo:

1. **Base de la pirámide (tests unitarios) con gate de cobertura**: una
   función de negocio (`app.py`, cálculo de descuentos de un carrito) y su
   suite de tests (`test_app.py`). Se corre local, en milisegundos, antes de
   cada commit, tal como describe la sección "Cómo funciona el shift left en
   la práctica".

2. **Test driven infrastructure**: `main.tf` define un security group y una
   base de datos en AWS con dos problemas típicos a propósito: un puerto SSH
   abierto a `0.0.0.0/0` y una credencial hardcodeada, los mismos dos casos
   que el post menciona en el ejemplo de la fintech ("no se exponían puertos
   innecesarios ni se usaban credenciales hardcodeadas"). El script
   `check_infra_tests.sh` valida la sintaxis con `terraform validate` y
   detecta ambos problemas SIN necesidad de credenciales de AWS ni de hacer
   `apply`.

3. **Gates de calidad en CI/CD**: `.github/workflows/ci-pipeline.yml` conecta
   ambos checks en un pipeline con dos jobs en paralelo. Si la cobertura cae
   por debajo del 80% o `check_infra_tests.sh` encuentra un problema, el job
   falla y bloquea el merge, igual que describe la sección "Mejores prácticas
   para maximizar el valor del shift left".

## Requisitos

- Python 3.10+ con `pip`
- Terraform >= 1.5 (opcional para el check de infraestructura completo; el
  script funciona parcialmente sin él, ver más abajo)
- No requiere cuenta de AWS ni credenciales reales: `terraform validate` no
  se conecta a ningún proveedor cloud

## Pasos para correrlo

### 1. Clonar y entrar al directorio

```bash
cd shift-left-testing-devops
```

### 2. Tests unitarios con gate de cobertura (80%)

```bash
pip install pytest pytest-cov
pytest test_app.py --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Salida esperada** (12 tests, cobertura 100%):

```
============================= test session starts ==============================
collected 12 items

test_app.py ............                                                  [100%]

-------- coverage: platform linux, python 3.x --------
Name     Stmts   Miss  Cover   Missing
--------------------------------------
app.py      14      0   100%
--------------------------------------
TOTAL       14      0   100%
Required test coverage of 80% reached. Total coverage: 100.00%

============================== 12 passed in 0.06s ===============================
```

### 3. Validación de infraestructura antes de aplicarla

```bash
chmod +x check_infra_tests.sh
./check_infra_tests.sh
```

`main.tf` tiene, a propósito, un puerto SSH abierto a internet y una
credencial hardcodeada. **Salida esperada** (el gate bloquea el problema
antes de que llegue a producción, como en el caso de la fintech del post):

```
== 1/3: terraform validate (sintaxis y sanidad del código) ==
OK: sintaxis de Terraform válida

== 2/3: puertos administrativos expuestos a internet ==
FALLO: puerto 22 (SSH) abierto a 0.0.0.0/0 en main.tf

== 3/3: credenciales hardcodeadas ==
FALLO: se encontró una credencial hardcodeada en main.tf

RESULTADO: 2 problema(s) encontrado(s). Gate de calidad BLOQUEADO.
```

El script termina con código de salida 1 (lo mismo que haría fallar un job
de CI). Si no tenés `terraform` instalado, el paso 1/3 se omite con un aviso
y los checks 2/3 y 3/3 (basados en grep) se ejecutan igual.

### 4. Corregir los problemas y volver a validar (opcional)

Para ver el gate en verde, editá `main.tf`:

- Cambiá `cidr_blocks = ["0.0.0.0/0"]` del bloque `ingress` del puerto 22
  por un rango interno, por ejemplo `["10.0.0.0/16"]`.
- Reemplazá la línea `password = "AKIAIOSFODNN7EXAMPLE"` por
  `password = var.db_password`, y agregá al final de `main.tf` la
  declaración de esa variable:

  ```hcl
  variable "db_password" {
    type      = string
    sensitive = true
  }
  ```

  En un uso real, el valor se provee vía `TF_VAR_db_password` o desde AWS
  Secrets Manager, nunca escrito en el archivo.

Y volvé a correr `./check_infra_tests.sh`: debería terminar con
`RESULTADO: todos los checks pasaron. Gate de calidad OK.`

### 5. Pipeline completo (opcional, requiere GitHub)

`.github/workflows/ci-pipeline.yml` conecta los dos checks anteriores en un
pipeline real. Para probarlo: copiar este repo a un repositorio de GitHub
con el workflow en `.github/workflows/` (ya está en esa ruta relativa a este
directorio) y hacer push; los dos jobs (`unit-tests` e `infra-tests`)
corren en paralelo en cada push o pull request a `main`.

## Notas

- El security group y la base de datos de `main.tf` son solo definiciones
  locales: en ningún paso de este ejemplo se ejecuta `terraform apply`, por
  lo que no se crea ningún recurso real en AWS ni se necesita cuenta.
- La credencial hardcodeada de `main.tf` es el valor de ejemplo público
  `AKIAIOSFODNN7EXAMPLE` que AWS documenta oficialmente para este tipo de
  demos, no una credencial real.
