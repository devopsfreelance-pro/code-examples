package soc2.controls

import rego.v1

# Politica como codigo (OPA) que valida un "terraform show -json" contra un
# control tipico de SOC2 Trust Services Criteria - CC6.1 (Logical Access /
# Confidentiality): los buckets S3 nuevos deben tener cifrado server-side,
# bloqueo de acceso publico y versionado habilitados.

s3_bucket_addrs contains name if {
	rc := input.resource_changes[_]
	rc.type == "aws_s3_bucket"
	not delete_only(rc)
	name := rc.change.after.bucket
}

delete_only(rc) if {
	count(rc.change.actions) == 1
	rc.change.actions[0] == "delete"
}

encrypted contains name if {
	rc := input.resource_changes[_]
	rc.type == "aws_s3_bucket_server_side_encryption_configuration"
	name := rc.change.after.bucket
}

public_access_blocked contains name if {
	rc := input.resource_changes[_]
	rc.type == "aws_s3_bucket_public_access_block"
	rc.change.after.block_public_acls == true
	rc.change.after.block_public_policy == true
	rc.change.after.ignore_public_acls == true
	rc.change.after.restrict_public_buckets == true
	name := rc.change.after.bucket
}

versioned contains name if {
	rc := input.resource_changes[_]
	rc.type == "aws_s3_bucket_versioning"
	some vc in rc.change.after.versioning_configuration
	vc.status == "Enabled"
	name := rc.change.after.bucket
}

deny contains msg if {
	some name in s3_bucket_addrs
	not name in encrypted
	msg := sprintf("SOC2 CC6.1: el bucket '%s' no tiene cifrado server-side configurado (aws_s3_bucket_server_side_encryption_configuration)", [name])
}

deny contains msg if {
	some name in s3_bucket_addrs
	not name in public_access_blocked
	msg := sprintf("SOC2 CC6.1: el bucket '%s' no bloquea el acceso publico (aws_s3_bucket_public_access_block con las 4 flags en true)", [name])
}

deny contains msg if {
	some name in s3_bucket_addrs
	not name in versioned
	msg := sprintf("SOC2 CC6.1: el bucket '%s' no tiene versionado habilitado (aws_s3_bucket_versioning)", [name])
}
