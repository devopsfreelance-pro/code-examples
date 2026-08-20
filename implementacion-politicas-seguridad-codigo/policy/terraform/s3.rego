package terraform.s3

import input as tfplan

# Regla de ENFORCE: bloquea el plan (exit code != 0 en conftest).
# Corresponde al paso 3 del post ("pasar a enforce con excepciones
# explicitas"): una vez que la politica esta probada, deny bloquea el merge.
deny[msg] {
	resource := tfplan.resource_changes[_]
	resource.type == "aws_s3_bucket_public_access_block"
	resource.change.after.block_public_acls == false
	msg := sprintf(
		"El bucket %s permite ACLs publicas: bloqueado por politica de seguridad",
		[resource.address],
	)
}

# Regla de AUDIT (warn): corresponde al paso 2 del post ("correr semanas en
# modo audit"). Reporta la misma condicion pero sin hacer fallar el pipeline;
# sirve para medir el impacto antes de activar el deny de arriba.
warn[msg] {
	resource := tfplan.resource_changes[_]
	resource.type == "aws_s3_bucket"
	not has_encryption(resource)
	msg := sprintf(
		"El bucket %s no tiene cifrado en reposo configurado (regla en modo audit, no bloquea)",
		[resource.address],
	)
}

has_encryption(resource) {
	resource.change.after.server_side_encryption_configuration
}
