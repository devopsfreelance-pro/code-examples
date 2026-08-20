package main

deny[msg] {
  input.kind == "Pod"
  container := input.spec.containers[_]
  not container.securityContext.runAsNonRoot
  msg := sprintf("Container %s must run as non-root", [container.name])
}

deny[msg] {
  input.kind == "Pod"
  container := input.spec.containers[_]
  container.securityContext.privileged
  msg := sprintf("Container %s must not be privileged", [container.name])
}

deny[msg] {
  input.kind == "Pod"
  container := input.spec.containers[_]
  not container.securityContext.readOnlyRootFilesystem
  msg := sprintf("Container %s must use read-only root filesystem", [container.name])
}
