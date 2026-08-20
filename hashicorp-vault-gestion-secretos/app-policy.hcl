path "secret/data/myapp/*" {
  capabilities = ["read", "list"]
}

path "database/creds/myapp-role" {
  capabilities = ["read"]
}

path "auth/token/renew-self" {
  capabilities = ["update"]
}
