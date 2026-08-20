# Progressive Delivery con Flagger: demo real en kind

Post: [Progressive Delivery: Guía Completa con Flagger 2025](https://www.devopsfreelance.pro/blog/posts/progressive-delivery-con-flagger/)

## Qué demuestra

El post explica que Flagger opera como un operador de Kubernetes que
convierte el progressive delivery en algo declarativo: definís un
recurso `Canary` con el Deployment a vigilar, y Flagger se encarga de
mover tráfico gradualmente hacia la nueva versión, corriendo checks en
cada paso y revirtiendo automáticamente si algo falla.

Este ejemplo instala **Flagger real** (no una simulación) en un cluster
`kind` local, usando el provider `kubernetes` (sin necesidad de instalar
Istio, que sería mucho más pesado para un mini-lab) y despliega:

1. `podinfo`, la app de ejemplo del propio creador de Flagger, como
   Deployment objetivo.
2. Un recurso `Canary` (`canary.yaml`) que declara el análisis: pasos de
   tráfico del 10% al 50% cada 15 segundos, un webhook `pre-rollout` que
   corre un smoke test, y un webhook `rollout` que genera carga contra la
   versión canary durante todo el análisis.
3. `flagger-loadtester`, el componente que ejecuta esos webhooks.

Al aplicar el `Canary`, Flagger clona automáticamente el Deployment en
`podinfo-primary` (versión estable) y gestiona `podinfo` como la versión
canary. Cuando cambiás la imagen de `podinfo`, Flagger detecta la
diferencia y arranca el rollout progresivo: podés verlo en vivo con
`kubectl get canary podinfo -n test --watch`, viendo el `STATUS` pasar
por `Progressing` y el `WEIGHT` subir de a 10 puntos, hasta `Succeeded`
(promoción al 100%) o `Failed` (rollback automático si el smoke test o
el load test fallan).

No se usa Istio/Linkerd para mantener el ejemplo liviano: por eso el
`Canary` no incluye las métricas estándar `request-success-rate` /
`request-duration` (que dependen de la telemetría del service mesh) y la
validación de cada paso se hace 100% vía webhooks, tal como documenta
Flagger para el modo "Kubernetes sin service mesh". El post cubre además
la integración con Istio (VirtualService/DestinationRule) para quien
quiera ese análisis basado en métricas de mesh.

## Requisitos

- Docker (o Podman) corriendo localmente.
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) instalado.
- `kubectl` instalado.
- [Helm](https://helm.sh/docs/intro/install/) instalado (se usa para
  instalar Flagger).
- Conexión a internet (para bajar las imágenes de Flagger, Prometheus,
  podinfo y el chart de Helm; todas son públicas y gratuitas).

No se necesita cuenta de nube ni credenciales.

## Pasos

### 1. Dar permisos de ejecución a los scripts

```bash
chmod +x setup.sh trigger-canary.sh
```

### 2. Levantar todo (cluster + Flagger + podinfo + Canary)

```bash
./setup.sh
```

Esto tarda unos minutos (crear el cluster, bajar imágenes, esperar a que
Flagger genere `podinfo-primary`). Al final vas a ver algo así:

```
NAME      STATUS      WEIGHT   LASTTRANSITIONTIME
podinfo   Initialized 0        2026-08-20T15:04:00Z
```

`Initialized` significa que Flagger ya clonó `podinfo` en
`podinfo-primary` y está en modo estable, esperando un cambio para
disparar el próximo canary.

### 3. Disparar un despliegue progresivo

```bash
./trigger-canary.sh
```

Este script cambia la imagen de `podinfo` a una versión nueva
(`6.6.0`) y sigue el estado del `Canary` en vivo. Vas a ver algo como:

```
NAME      STATUS       WEIGHT   LASTTRANSITIONTIME
podinfo   Progressing  0        2026-08-20T15:10:15Z
podinfo   Progressing  0        2026-08-20T15:10:30Z
podinfo   Progressing  0        2026-08-20T15:10:45Z
podinfo   Promoting    0        2026-08-20T15:11:00Z
podinfo   Finalising   0        2026-08-20T15:11:15Z
podinfo   Succeeded    0        2026-08-20T15:11:30Z
```

Con el provider `kubernetes` (sin service mesh), Flagger no mueve
tráfico por peso: el propio operador loguea "Progressive traffic is not
supported when using the kubernetes provider" y en su lugar hace un
análisis por iteraciones al estilo blue/green (`stepWeight`/`maxWeight`
quedan definidos en `canary.yaml` mismo, pero se ignoran con este
provider). `WEIGHT` se mantiene en `0` durante todo el proceso; podés
seguir el avance real por las iteraciones (`Advance podinfo.test canary
iteration N/10`) en `kubectl -n test describe canary podinfo` o en los
logs de Flagger. Cuando el `STATUS` llega a `Succeeded`, Flagger corrió
el smoke test y el load test durante todas las iteraciones sin fallos y
promovió la nueva versión a `podinfo-primary` de una vez. Si querés ver
tráfico moviéndose por peso real (10% → 20% → ... 50%), necesitás un
service mesh como Istio (`meshProvider=istio`), que el post cubre por
separado. Cortá el `--watch` con `Ctrl+C` cuando veas `Succeeded`.

En otra terminal podés ver los eventos y el detalle de cada webhook:

```bash
kubectl -n test describe canary podinfo
kubectl -n flagger-system logs deploy/flagger -f
```

### 4. (Opcional) Provocar un rollback automático

Desplegá una imagen que falle el `readinessProbe` a propósito (un tag
que no existe hace que los pods nunca queden `Ready`):

```bash
kubectl set image deployment/podinfo podinfod=ghcr.io/stefanprodan/podinfo:no-existe -n test
kubectl get canary podinfo -n test --watch
```

Como los pods canary nunca pasan el health check, Flagger no puede
progresar el `WEIGHT`. Después de `threshold: 5` intentos fallidos
seguidos (definido en `canary.yaml`), el `STATUS` pasa a `Failed` y
Flagger revierte el tráfico al 0% sin intervención manual: exactamente
el comportamiento de "red de seguridad automática" que describe el post.

### 5. Limpiar

```bash
kind delete cluster --name flagger-demo
```

## Archivos

- `kind-config.yaml`: cluster kind de un solo nodo.
- `podinfo.yaml`: Deployment objetivo del canary (la app de ejemplo
  `podinfo`).
- `canary.yaml`: el recurso `Canary` de Flagger (análisis, pesos,
  webhooks) más el `flagger-loadtester` que ejecuta esos webhooks.
- `setup.sh`: crea el cluster, instala Flagger vía Helm y despliega
  podinfo + el Canary.
- `trigger-canary.sh`: cambia la imagen de podinfo y sigue el rollout
  progresivo en vivo.

## Notas

- Se usa el provider `meshProvider=kubernetes` de Flagger, que no
  requiere Istio/Linkerd/App Mesh: es la opción más liviana para probar
  el concepto en una laptop. El post detalla también la integración con
  Istio (`VirtualService`/`DestinationRule`) para quien quiera análisis
  basado en métricas de mesh (`request-success-rate`,
  `request-duration`) en vez de solo webhooks.
- Las imágenes usadas (`podinfo`, `flagger`, `flagger-loadtester`) son
  públicas y mantenidas por el proyecto Flagger
  (`github.com/fluxcd/flagger`), sin costo ni registro necesario.
