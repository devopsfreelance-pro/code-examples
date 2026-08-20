package main

# Policy as code (nivel 3 de la pirámide del post): reglas organizacionales
# evaluadas sobre el `terraform plan`, no sobre el código fuente.
# Corre con: terraform show -json tfplan | conftest test -p policy/ -
#
# Simplificada a propósito para un solo bucket de demo: en un repo real
# cada regla recorrería todos los aws_s3_bucket del plan y matchearía
# cada uno contra su propia configuración de encriptación/acceso público
# por dirección del módulo, no por nombre fijo.

encryption_resources_created := [r |
	r := input.resource_changes[_]
	r.type == "aws_s3_bucket_server_side_encryption_configuration"
	r.change.actions[_] != "delete"
]

bucket_resources_created := [r |
	r := input.resource_changes[_]
	r.type == "aws_s3_bucket"
	r.change.actions[_] != "delete"
]

deny[msg] {
	count(bucket_resources_created) > 0
	count(encryption_resources_created) == 0
	msg := "Hay al menos un aws_s3_bucket en el plan sin aws_s3_bucket_server_side_encryption_configuration asociado"
}

deny[msg] {
	pab := input.resource_changes[_]
	pab.type == "aws_s3_bucket_public_access_block"
	pab.change.actions[_] != "delete"
	pab.change.after.block_public_acls != true
	msg := sprintf(
		"El bucket asociado a '%s' no bloquea ACLs públicas (block_public_acls debe ser true)",
		[pab.address],
	)
}
