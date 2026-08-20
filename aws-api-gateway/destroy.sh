#!/usr/bin/env bash
# Destruye los recursos creados y limpia artefactos locales.
set -euo pipefail

cd "$(dirname "$0")"

terraform destroy -auto-approve
rm -f lambda.zip
