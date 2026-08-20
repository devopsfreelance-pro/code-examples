package terraform.aws

import rego.v1

deny contains msg if {
  resource := input.resource_changes[_]
  resource.type == "aws_s3_bucket"
  not resource.change.after.server_side_encryption_configuration
  msg := sprintf("S3 bucket '%s' must have encryption enabled", [resource.name])
}

deny contains msg if {
  resource := input.resource_changes[_]
  resource.type == "aws_instance"
  not resource.change.after.tags.Environment
  msg := sprintf("Instance '%s' is missing required 'Environment' tag", [resource.name])
}
