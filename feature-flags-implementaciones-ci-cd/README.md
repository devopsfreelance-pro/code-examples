# Feature Flags en CI/CD - Ejemplo ejecutable

Post: [Feature Flags en CI/CD: Guía Completa para Despliegues Seguros](https://www.devopsfreelance.pro/blog/posts/feature-flags-implementaciones-ci-cd/)

## Qué demuestra

Este ejemplo implementa un cliente de feature flags mínimo pero real, sin
depender de un SaaS de pago (LaunchDarkly, Split.io) ni de infraestructura
externa. Ilustra los conceptos centrales del post:

- **Separar despliegue de liberación**: el código de `new-dashboard-design`
  ya está desplegado, pero solo se activa según reglas del flag.
- **Rollout progresivo por porcentaje**: `flags.json` define que
  `new-dashboard-design` está activo para el 25% de los usuarios.
- **Sticky bucketing**: un mismo `user_id` cae siempre en la misma variante
  (hash SHA-256 determinista), en vez de una moneda al aire en cada request.
- **Cache local con TTL**: el cliente no relee el archivo de flags en cada
  evaluación, simula el patrón caché-en-memoria + recarga periódica que
  describe el post como alternativa a streaming/websockets.
- **Ops toggle / kill switch**: `maintenance-mode` como flag apagado por
  defecto, para desactivar algo instantáneamente sin rollback de código.

## Requisitos

- Python 3.8 o superior (sin dependencias externas, solo librería estándar)

## Cómo correrlo

```bash
cd feature-flags-implementaciones-ci-cd
python3 demo.py
```

## Salida esperada

Los flags cargados y el mensaje de sticky bucketing son deterministas.
El porcentaje de rollout va a variar levemente entre corridas porque
`demo.py` simula 2000 usuarios distintos (`user-0` a `user-1999`) contra un
hash uniforme, pero siempre debería rondar el 25% configurado en
`flags.json`:

```
=== Flags cargados desde flags.json ===
  new-dashboard-design: enabled=True rollout=25% - Nuevo diseño de dashboard (release toggle)
  checkout-experiment-b: enabled=True rollout=50% - Variante B del checkout (experiment toggle A/B)
  maintenance-mode: enabled=False rollout=100% - Kill switch de emergencia (ops toggle)

=== Rollout observado: new-dashboard-design ===
  476/2000 usuarios (23.8%) ven la v2
  Configurado en flags.json: 25% -> esperado ~25% (hash uniforme)

=== Sticky bucketing: mismo usuario, misma variante siempre ===
  user-1 -> version v1
  user-1 -> version v1
  user-1 -> version v1

=== Kill switch: ops toggle apagado ===
  maintenance-mode enabled para user-1: False
```

## Probar el rollout progresivo

Editá `flags.json` y subí `rollout_percentage` de `new-dashboard-design` a,
por ejemplo, `80`, volvé a correr `python3 demo.py` y confirmá que ahora
~80% de los usuarios ven la v2. Esto simula el proceso real de un rollout
gradual: empezar en 5-10%, monitorear métricas, y subir el porcentaje hasta
el 100%.

## Archivos

- `flags.json`: configuración de flags (equivalente al panel de control /
  servicio centralizado que describe el post).
- `feature_flags.py`: `FeatureFlagClient`, el SDK que evalúa flags con
  rollout por porcentaje y sticky bucketing.
- `demo.py`: `UserService` de ejemplo (el mismo del snippet del post) más
  la simulación de tráfico que valida el comportamiento.
