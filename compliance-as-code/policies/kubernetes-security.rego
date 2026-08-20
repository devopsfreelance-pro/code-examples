package main

# Política de compliance as code para Kubernetes, adaptada del post para
# correr con `conftest` (recibe el manifiesto YAML crudo, no un
# AdmissionReview de un webhook real).
#
# Reglas:
#   1. Todo contenedor debe declarar securityContext.runAsNonRoot = true.
#   2. Ningún contenedor puede correr en modo privileged.

deny[msg] {
	input.kind == "Pod"
	container := input.spec.containers[_]
	not container.securityContext.runAsNonRoot
	msg := sprintf("El contenedor '%v' debe ejecutarse como usuario no-root (securityContext.runAsNonRoot: true)", [container.name])
}

deny[msg] {
	input.kind == "Pod"
	container := input.spec.containers[_]
	container.securityContext.privileged
	msg := sprintf("El contenedor '%v' no puede ejecutarse en modo privilegiado (securityContext.privileged: true)", [container.name])
}
