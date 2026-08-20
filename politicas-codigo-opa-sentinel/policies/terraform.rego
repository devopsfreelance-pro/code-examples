package terraform

# Politica: los buckets S3 deben tener cifrado del lado del servidor habilitado.
deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_s3_bucket"
    not resource.change.after.server_side_encryption_configuration
    msg := sprintf("Bucket S3 '%s' debe tener cifrado habilitado", [resource.address])
}

# Politica: prohibido usar el tipo de instancia t3.2xlarge (control de costos).
deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_instance"
    resource.change.after.instance_type == "t3.2xlarge"
    msg := sprintf("Instancia '%s' usa tipo prohibido t3.2xlarge", [resource.address])
}
