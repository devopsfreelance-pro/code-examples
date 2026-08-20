# Serverless vs Microservices: Cost Calculator and Decision Matrix

Post: [Serverless vs Microservices: How to Choose in 2026](https://www.devopsfreelance.pro/blog/en/posts/serverless-vs-microservices/)

## What this example demonstrates

The post lays out two concrete, quantifiable axes for deciding between serverless
and containerized microservices: **cost based on traffic volume** and **a decision
matrix** of questions to pick an architecture. This example implements both with
executable Python scripts (no external dependencies):

- **`cost_calculator.py`**: calculates the real monthly cost of AWS Lambda (pay
  per invocation + GB-second) vs AWS Fargate (pay per vCPU-hour + GB-hour,
  always-on containers), using AWS pricing formulas. It reproduces the post's
  conclusion: *"serverless is cheaper with low or variable traffic, containerized
  microservices are cheaper with high, constant traffic"*.
- **`decision_matrix.py`**: asks the same 10 questions from the post's "Decision
  Matrix" section (constant traffic > 10K req/min? need WebSockets? small team
  without infra? etc.), tallies points per architecture, and recommends
  microservices, serverless, or a hybrid pattern in case of a tie.

## Requirements

- Python 3.8+ (no external dependencies, standard library only)

## Steps to run it

```bash
# 1. Verify syntax (optional)
python3 -m py_compile cost_calculator.py decision_matrix.py

# 2. Cost with low traffic (1M requests/month, default values:
#    100ms duration, 256MB memory, 2 Fargate replicas)
python3 cost_calculator.py 1000000

# 3. Cost with high traffic (100M requests/month, 150ms, 512MB, 3 replicas)
python3 cost_calculator.py 100000000 150 512 3

# 4. Decision matrix in demo mode (no interactive input)
python3 decision_matrix.py --demo

# 5. Interactive decision matrix (answer y/N to each question)
python3 decision_matrix.py
```

## Expected output

### `cost_calculator.py 1000000`

```
Trafico simulado: 1,000,000 requests/mes
Lambda:    duracion=100.0ms, memoria=256MB
Fargate:   2 replicas x 0.5 vCPU / 0.5GB, siempre encendidas

  Costo mensual Lambda (serverless):        $0.42
  Costo mensual Fargate (microservicios):   $32.80

Serverless es ~99% mas barato a este volumen (1,000,000 req/mes).
```

### `cost_calculator.py 100000000 150 512 3`

```
Trafico simulado: 100,000,000 requests/mes
Lambda:    duracion=150.0ms, memoria=512MB
Fargate:   3 replicas x 0.5 vCPU / 0.5GB, siempre encendidas

  Costo mensual Lambda (serverless):        $144.80
  Costo mensual Fargate (microservicios):   $49.19

Microservicios en contenedores son ~66% mas baratos a este volumen (100,000,000 req/mes). El costo fijo de los contenedores siempre encendidos ya se amortiza.
```

The relationship flips depending on volume, just as the post's cost table
describes: at low traffic serverless wins (it pays almost nothing), at high
traffic the fixed, predictable cost of containers wins.

### `decision_matrix.py --demo`

```
Modo demo (respuestas de ejemplo: equipo chico, trafico variable):

  Trafico constante > 10K req/min? [s/N]: n
  Procesos > 15 minutos? [s/N]: n
  Necesitas WebSockets? [s/N]: n
  Equipo DevOps dedicado? [s/N]: n
  Trafico variable o esporadico? [s/N]: s
  Event-driven processing? [s/N]: s
  Equipo pequeno sin infra? [s/N]: s
  Time-to-market es prioridad? [s/N]: s
  Multi-cloud obligatorio? [s/N]: n
  Presupuesto ajustado, bajo uso? [s/N]: s

Puntaje microservicios: 0/10
Puntaje serverless:     5/10

Recomendacion: serverless (5 vs 0).
```

Note: the scripts' own console output is in Spanish (variable labels like
`Trafico simulado`, `Costo mensual`); only this README has been translated.
The numbers and behavior are identical regardless of language.

## What this example does NOT demonstrate

Lambda and Fargate prices are hardcoded as an approximate reference
(us-east-1, 2026) to illustrate the cost relationship, not for real
billing: always check the official AWS pricing calculator before
budgeting. The number of Fargate replicas in `cost_calculator.py` is
fixed (it doesn't auto-scale with simulated traffic); in a real scenario
of 100M requests/month you'd need to size replicas based on actual
capacity, not a fixed value. The goal is to show the direction of the
trade-off (low traffic → serverless wins; high, constant traffic →
containers win), not to replace real capacity planning analysis.

## No accounts or secrets required

This example requires no AWS account and no paid service: it's a local
mathematical simulation using AWS's published pricing formulas.

---

## 🇪🇸 Versión en español

# Serverless vs Microservicios: calculadora de costos y matriz de decisión

Post: [Serverless vs Microservicios: Cuál Elegir y Cuándo (2026)](https://www.devopsfreelance.pro/blog/posts/serverless-vs-microservicios/)

## Qué demuestra este ejemplo

El post plantea dos ejes concretos y cuantificables para decidir entre serverless
y microservicios en contenedores: **el costo según el volumen de tráfico** y
**una matriz de preguntas** para elegir arquitectura. Este ejemplo implementa
ambos con scripts Python ejecutables (sin dependencias externas):

- **`cost_calculator.py`**: calcula el costo mensual real de AWS Lambda (pago
  por invocación + GB-segundo) vs AWS Fargate (pago por vCPU-hora + GB-hora,
  contenedores siempre encendidos), usando las fórmulas de pricing de AWS.
  Reproduce la conclusión del post: *"serverless es más barato con tráfico bajo
  o variable, microservicios en contenedores son más baratos con tráfico alto y
  constante"*.
- **`decision_matrix.py`**: hace las mismas 10 preguntas de la sección "Matriz
  de Decisión" del post (¿tráfico constante > 10K req/min?, ¿necesitás
  WebSockets?, ¿equipo pequeño sin infra?, etc.), suma puntos por arquitectura
  y recomienda microservicios, serverless, o un patrón híbrido en caso de
  empate.

## Requisitos

- Python 3.8+ (sin dependencias externas, solo librería estándar)

## Pasos para correrlo

```bash
# 1. Verificar sintaxis (opcional)
python3 -m py_compile cost_calculator.py decision_matrix.py

# 2. Costo con tráfico bajo (1M requests/mes, valores por defecto:
#    100ms de duración, 256MB de memoria, 2 réplicas Fargate)
python3 cost_calculator.py 1000000

# 3. Costo con tráfico alto (100M requests/mes, 150ms, 512MB, 3 réplicas)
python3 cost_calculator.py 100000000 150 512 3

# 4. Matriz de decisión en modo demo (sin input interactivo)
python3 decision_matrix.py --demo

# 5. Matriz de decisión interactiva (responde s/N a cada pregunta)
python3 decision_matrix.py
```

## Salida esperada

### `cost_calculator.py 1000000`

```
Trafico simulado: 1,000,000 requests/mes
Lambda:    duracion=100.0ms, memoria=256MB
Fargate:   2 replicas x 0.5 vCPU / 0.5GB, siempre encendidas

  Costo mensual Lambda (serverless):        $0.42
  Costo mensual Fargate (microservicios):   $32.80

Serverless es ~99% mas barato a este volumen (1,000,000 req/mes).
```

### `cost_calculator.py 100000000 150 512 3`

```
Trafico simulado: 100,000,000 requests/mes
Lambda:    duracion=150.0ms, memoria=512MB
Fargate:   3 replicas x 0.5 vCPU / 0.5GB, siempre encendidas

  Costo mensual Lambda (serverless):        $144.80
  Costo mensual Fargate (microservicios):   $49.19

Microservicios en contenedores son ~66% mas baratos a este volumen (100,000,000 req/mes). El costo fijo de los contenedores siempre encendidos ya se amortiza.
```

La relación se invierte según el volumen, tal como describe la tabla de
costos del post: a bajo tráfico gana serverless (paga casi nada), a tráfico
alto gana el costo fijo y predecible de los contenedores.

### `decision_matrix.py --demo`

```
Modo demo (respuestas de ejemplo: equipo chico, trafico variable):

  Trafico constante > 10K req/min? [s/N]: n
  Procesos > 15 minutos? [s/N]: n
  Necesitas WebSockets? [s/N]: n
  Equipo DevOps dedicado? [s/N]: n
  Trafico variable o esporadico? [s/N]: s
  Event-driven processing? [s/N]: s
  Equipo pequeno sin infra? [s/N]: s
  Time-to-market es prioridad? [s/N]: s
  Multi-cloud obligatorio? [s/N]: n
  Presupuesto ajustado, bajo uso? [s/N]: s

Puntaje microservicios: 0/10
Puntaje serverless:     5/10

Recomendacion: serverless (5 vs 0).
```

## Qué NO demuestra este ejemplo

Los precios de Lambda y Fargate están hardcodeados como referencia
aproximada (us-east-1, 2026) para ilustrar la relación de costos, no para
facturación real: consultá siempre la calculadora de precios oficial de AWS
antes de presupuestar. El número de réplicas Fargate en `cost_calculator.py`
es fijo (no escala automáticamente con el tráfico simulado); en un escenario
real de 100M requests/mes necesitarías dimensionar réplicas según capacidad
real, no un valor fijo. El objetivo es mostrar la dirección del trade-off
(bajo tráfico → serverless gana; tráfico alto y constante → contenedores
ganan), no reemplazar un análisis de capacity planning real.

## Sin cuentas ni secretos

Este ejemplo no requiere cuenta de AWS ni ningún servicio pago: es una
simulación matemática local con las fórmulas de pricing publicadas por AWS.
