"""Mismo recurso que terraform/main.tf, pero escrito en Python con Pulumi.

Levanta un contenedor nginx local. Sirve para comparar en la práctica cómo
se ve "el mismo recurso" en cada herramienta: HCL declarativo vs Python
imperativo/declarativo con tipos y estructuras de control reales.
"""

import pulumi
import pulumi_docker as docker

config = pulumi.Config()
container_name = config.get("containerName") or "web-server-pulumi"
external_port = config.get_int("externalPort") or 8082

image = docker.RemoteImage(
    "nginx",
    name="nginx:alpine",
    keep_locally=True,
)

web_server = docker.Container(
    "web-server",
    name=container_name,
    image=image.image_id,
    ports=[
        docker.ContainerPortArgs(
            internal=80,
            external=external_port,
        )
    ],
)

pulumi.export("url", pulumi.Output.concat("http://localhost:", str(external_port)))
pulumi.export("container_id", web_server.id)
