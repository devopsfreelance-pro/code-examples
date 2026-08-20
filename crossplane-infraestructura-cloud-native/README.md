# Crossplane: infraestructura cloud-native con Kubernetes como control plane

Codigo de ejemplo del post [Crossplane: Guia completa para infraestructura cloud-native](https://www.devopsfreelance.pro/blog/posts/crossplane-infraestructura-cloud-native/).

## Que demuestra este ejemplo

El post explica los tres pilares de Crossplane: **XRD** (define una API de
infraestructura custom), **Composition** (traduce esa API en recursos
concretos) y **Claim** (lo que pide un desarrollador). Este ejemplo los pone
en funcionamiento en un cluster local:

1. Un `CompositeResourceDefinition` (`00-xrd.yaml`) define el recurso
   `AppDatabase`, con dos parametros simples: `engine` y `size`.
2. Una `Composition` (`01-composition.yaml`) traduce ese `AppDatabase` en
   dos recursos concretos: un `ConfigMap` (simula el endpoint de la base de
   datos) y un `Secret` (simula las credenciales). En un entorno real estos
   recursos serian, por ejemplo, una instancia de AWS RDS y su grupo de
   seguridad.
3. Un `Claim` (`03-claim.yaml`) es lo que pediria un desarrollador de
   aplicaciones: "quiero una AppDatabase postgres, tamano small", sin saber
   que hay detras.

Para que el ejemplo corra sin cuentas cloud ni costos, en vez de un provider
de AWS/Azure/GCP se usa
[`provider-kubernetes`](https://github.com/crossplane-contrib/provider-kubernetes),
que le permite a Crossplane crear recursos de Kubernetes como si fueran
infraestructura externa. El patron (XRD -> Composition -> Claim -> recursos
reconciliados) es identico al que se usaria con un provider cloud real.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/)
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) (Kubernetes in Docker)
- [kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl)
- [Helm](https://helm.sh/docs/intro/install/) (para instalar Crossplane)

No hace falta cuenta de AWS/Azure/GCP ni ningun secreto: todo corre en un
cluster kind local.

## Pasos para correrlo

```bash
cd crossplane-infraestructura-cloud-native

# 1. Levanta el cluster kind, instala Crossplane + provider-kubernetes,
#    aplica el XRD, la Composition y el Claim de ejemplo.
./run-demo.sh
```

El script tarda entre 2 y 4 minutos (descarga de imagenes de Crossplane y
del provider incluida) y al final imprime:

- El `Claim` (`appdatabase/demo-app-db`) con su estado.
- El recurso compuesto (`XAppDatabase`) generado por Crossplane a partir del claim.
- Los `Object` gestionados por `provider-kubernetes` (el ConfigMap y el Secret).
- El contenido del ConfigMap que simula el endpoint de la base de datos.

### Verificacion manual (opcional)

```bash
# Ver el claim
kubectl get appdatabase demo-app-db -n default

# Ver el recurso compuesto que crea Crossplane
kubectl get xappdatabases.example.org

# Ver los recursos "cloud" simulados
kubectl get configmap demo-app-db-endpoint -n default -o yaml
kubectl get secret demo-app-db-credentials -n default -o yaml

# Ver eventos de reconciliacion
kubectl describe appdatabase demo-app-db -n default
```

### Salida esperada (resumen)

```
--- Claim ---
NAME          SYNCED   READY   CONNECTION-SECRET   AGE
demo-app-db   True     True                        45s

--- Composite resource (XR) generado ---
NAME                     SYNCED   READY   COMPOSITION                  AGE
xappdatabases-xxxxx      True     True    xappdatabases.example.org   45s

--- Recursos gestionados (Objects del provider-kubernetes) ---
NAME                                  SYNCED   READY
demo-app-db-endpoint-xxxxx            True     True
demo-app-db-credentials-xxxxx         True     True

--- ConfigMap simulando el endpoint de la 'base de datos' ---
apiVersion: v1
kind: ConfigMap
metadata:
  name: demo-app-db-endpoint
  namespace: default
data:
  engine: postgres
  size: small
  host: placeholder.svc.cluster.local
  port: "5432"
```

### Limpieza

```bash
./cleanup.sh
```

Esto borra el cluster kind completo (`crossplane-demo`), sin dejar nada
residual en el equipo.

## Archivos

| Archivo | Descripcion |
|---|---|
| `00-xrd.yaml` | CompositeResourceDefinition: define la API `AppDatabase` |
| `01-composition.yaml` | Composition: traduce `AppDatabase` en ConfigMap + Secret |
| `02-provider-kubernetes.yaml` | Instala `provider-kubernetes` y su ProviderConfig |
| `03-claim.yaml` | Claim de ejemplo que pediria un desarrollador |
| `run-demo.sh` | Script que levanta todo el entorno y aplica los manifests en orden |
| `cleanup.sh` | Borra el cluster kind |

## Notas

- La version del paquete `provider-kubernetes` esta fijada en
  `v0.13.0` en `02-provider-kubernetes.yaml`. Si al correr `run-demo.sh` el
  provider no llega a `Healthy`, revisar la lista de tags disponibles en
  https://marketplace.upbound.io/providers/crossplane-contrib/provider-kubernetes
  y actualizar la version en ese archivo.
- El Secret creado (`demo-app-db-credentials`) tiene una contrasena de
  ejemplo en texto plano (`demo-password-not-for-production`) solo para
  fines didacticos. En un entorno real, las credenciales de un provider
  cloud nunca se hardcodean asi: se gestionan con un sistema de secretos
  (Vault, AWS Secrets Manager) como se menciona en el post.
