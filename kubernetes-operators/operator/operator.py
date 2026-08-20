#!/usr/bin/env python3
"""
Mini Kubernetes Operator para el CRD `Database` (example.com/v1alpha1).

Implementa el ciclo de reconciliación descrito en el post:
  1. Observación: watch sobre los Custom Resources Database
  2. Analisis: compara el estado deseado (spec) con el actual (Deployment/Service)
  3. Ejecucion: crea o actualiza el Deployment y el Service correspondientes
  4. Actualizacion de estado: escribe status.phase en el Custom Resource
  5. Requeue: vuelve a observar en el siguiente evento (o cada RESYNC_SECONDS)

Uso:
    pip install kubernetes
    python3 operator.py
"""
import logging
import time

from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException

GROUP = "example.com"
VERSION = "v1alpha1"
PLURAL = "databases"
NAMESPACE = "default"
RESYNC_SECONDS = 30

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [operator] %(levelname)s %(message)s",
)
log = logging.getLogger("database-operator")


def build_deployment(name: str, spec: dict) -> client.V1Deployment:
    image = spec["image"]
    replicas = spec.get("replicas", 1)
    port = spec.get("port", 5432)

    labels = {"app": name, "managed-by": "database-operator"}

    container = client.V1Container(
        name="database",
        image=image,
        ports=[client.V1ContainerPort(container_port=port)],
        env=[client.V1EnvVar(name="POSTGRES_PASSWORD", value="demo-password")],
    )
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels=labels),
        spec=client.V1PodSpec(containers=[container]),
    )
    spec_obj = client.V1DeploymentSpec(
        replicas=replicas,
        selector=client.V1LabelSelector(match_labels=labels),
        template=template,
    )
    return client.V1Deployment(
        metadata=client.V1ObjectMeta(name=name, labels=labels),
        spec=spec_obj,
    )


def build_service(name: str, spec: dict) -> client.V1Service:
    port = spec.get("port", 5432)
    labels = {"app": name, "managed-by": "database-operator"}
    return client.V1Service(
        metadata=client.V1ObjectMeta(name=name, labels=labels),
        spec=client.V1ServiceSpec(
            selector={"app": name},
            ports=[client.V1ServicePort(port=port, target_port=port)],
        ),
    )


def reconcile_deployment(apps_api: client.AppsV1Api, name: str, spec: dict):
    deployment = build_deployment(name, spec)
    try:
        apps_api.create_namespaced_deployment(NAMESPACE, deployment)
        log.info("Deployment '%s' creado", name)
    except ApiException as e:
        if e.status == 409:
            apps_api.replace_namespaced_deployment(name, NAMESPACE, deployment)
            log.info("Deployment '%s' actualizado (reconciliado)", name)
        else:
            raise


def reconcile_service(core_api: client.CoreV1Api, name: str, spec: dict):
    service = build_service(name, spec)
    try:
        core_api.create_namespaced_service(NAMESPACE, service)
        log.info("Service '%s' creado", name)
    except ApiException as e:
        if e.status == 409:
            log.info("Service '%s' ya existe, sin cambios", name)
        else:
            raise


def update_status(custom_api: client.CustomObjectsApi, name: str, phase: str, replicas: int):
    body = {
        "status": {
            "phase": phase,
            "observedReplicas": replicas,
            "lastReconcileTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    }
    try:
        custom_api.patch_namespaced_custom_object_status(
            GROUP, VERSION, NAMESPACE, PLURAL, name, body
        )
    except ApiException as e:
        log.warning("No se pudo actualizar status de '%s': %s", name, e.reason)


def reconcile(apps_api, core_api, custom_api, name: str, spec: dict):
    log.info("Reconciliando Database '%s' (image=%s, replicas=%s)",
              name, spec.get("image"), spec.get("replicas", 1))
    reconcile_deployment(apps_api, name, spec)
    reconcile_service(core_api, name, spec)
    update_status(custom_api, name, "Ready", spec.get("replicas", 1))
    log.info("Database '%s' reconciliada -> status.phase=Ready", name)


def delete_children(apps_api, core_api, name: str):
    for fn, label in (
        (lambda: apps_api.delete_namespaced_deployment(name, NAMESPACE), "Deployment"),
        (lambda: core_api.delete_namespaced_service(name, NAMESPACE), "Service"),
    ):
        try:
            fn()
            log.info("%s '%s' eliminado", label, name)
        except ApiException as e:
            if e.status != 404:
                log.warning("Error eliminando %s '%s': %s", label, name, e.reason)


def main():
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()

    apps_api = client.AppsV1Api()
    core_api = client.CoreV1Api()
    custom_api = client.CustomObjectsApi()

    log.info("Operator iniciado. Observando Database en namespace '%s'...", NAMESPACE)

    while True:
        w = watch.Watch()
        try:
            for event in w.stream(
                custom_api.list_namespaced_custom_object,
                GROUP, VERSION, NAMESPACE, PLURAL,
                timeout_seconds=RESYNC_SECONDS,
            ):
                obj = event["object"]
                event_type = event["type"]
                name = obj["metadata"]["name"]
                spec = obj.get("spec", {})

                if event_type in ("ADDED", "MODIFIED"):
                    reconcile(apps_api, core_api, custom_api, name, spec)
                elif event_type == "DELETED":
                    log.info("Database '%s' eliminada, limpiando recursos hijos", name)
                    delete_children(apps_api, core_api, name)
        except ApiException as e:
            log.error("Error del API server: %s", e.reason)
            time.sleep(5)
        except Exception as e:  # noqa: BLE001 - operator debe seguir vivo ante errores transitorios
            log.error("Error inesperado en el watch loop: %s", e)
            time.sleep(5)


if __name__ == "__main__":
    main()
