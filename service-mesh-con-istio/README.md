# Service Mesh con Istio: canary routing por header

Ejemplo ejecutable que acompaña al post
[Guía Completa de Service mesh con Istio](https://www.devopsfreelance.pro/blog/posts/service-mesh-con-istio/).

## Qué demuestra

El post explica que Istio permite enrutar tráfico entre versiones de un mismo
servicio sin tocar el código de la aplicación, usando los recursos
`VirtualService` y `DestinationRule`, e incluye como ejemplo un
`VirtualService` que dirige al usuario `jason` (header `end-user: jason`) a la
versión `v2` de un servicio `reviews`, y al resto del tráfico a la versión
`v1`.

Este directorio levanta ese escenario completo en un cluster local:

- Dos versiones (`v1` y `v2`) del servicio `reviews` corriendo en paralelo.
- Istio en perfil `demo`, con inyección automática de sidecars en el
  namespace `default`.
- Un `DestinationRule` que define los subsets `v1`/`v2` por label `version`.
- El mismo `VirtualService` del post: header `end-user: jason` → `v2`,
  cualquier otro request → `v1`.
- Un pod cliente (`sleep`) dentro de la malla para probar el enrutamiento
  con `curl`.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/)
- [kind](https://kind.sigs.k8s.io/) (Kubernetes en Docker)
- [kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl)
- [istioctl](https://istio.io/latest/docs/setup/getting-started/#download)

Para instalar `istioctl` (mismo comando que usa el post):

```bash
curl -L https://istio.io/downloadIstio | sh -
export PATH="$PWD/istio-"*"/bin:$PATH"
```

No se necesita cuenta ni credencial de ningún proveedor cloud: todo corre en
contenedores locales.

## Pasos para correrlo

Desde este directorio (`service-mesh-con-istio/`):

```bash
chmod +x setup.sh
./setup.sh
```

El script hace, en orden:

1. Crea el cluster `kind` (`kind-config.yaml`).
2. Instala Istio con `istioctl install --set profile=demo -y`.
3. Etiqueta el namespace `default` con `istio-injection=enabled`.
4. Aplica `reviews-app.yaml` (deployments `reviews-v1`/`reviews-v2`, el
   `Service` compartido `reviews` y el pod `sleep`).
5. Aplica `istio-routing.yaml` (`DestinationRule` + `VirtualService`).
6. Ejecuta dos `curl` de prueba desde el pod `sleep`.

## Salida esperada

El primer `curl` (sin header) debe responder con el hostname de un pod
`reviews-v1-...`:

```
==> Prueba 1: request sin header 'end-user' -> debe responder reviews-v1
Hostname: reviews-v1-7d9f8c9d6b-abcde
```

El segundo `curl` (con `end-user: jason`) debe responder con el hostname de
un pod `reviews-v2-...`:

```
==> Prueba 2: request con header 'end-user: jason' -> debe responder reviews-v2
Hostname: reviews-v2-6f8b7c5d4a-fghij
```

Podés repetir las pruebas manualmente cuantas veces quieras:

```bash
# Sin header -> siempre v1
kubectl exec sleep -c curl -- curl -s reviews | grep Hostname

# Con header -> siempre v2
kubectl exec sleep -c curl -- curl -s -H "end-user: jason" reviews | grep Hostname
```

## Limpieza

```bash
kind delete cluster --name istio-demo
```

## Archivos

- `kind-config.yaml` — cluster local de un solo nodo.
- `reviews-app.yaml` — deployments `reviews-v1`/`reviews-v2`, `Service`
  `reviews` y pod cliente `sleep`.
- `istio-routing.yaml` — `DestinationRule` (subsets v1/v2) y `VirtualService`
  (routing por header, igual al ejemplo del post).
- `setup.sh` — orquesta todo el flujo de arriba.
