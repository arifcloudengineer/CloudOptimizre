#!/usr/bin/env bash
# Tears down CloudOptimizer infrastructure. Destructive -- asks for confirmation.
set -euo pipefail

ENVIRONMENT="${1:-dev}"
TF_DIR="terraform/environments/${ENVIRONMENT}"

if [ ! -d "$TF_DIR" ]; then
  echo "No environment '${ENVIRONMENT}' found under terraform/environments/"
  exit 1
fi

cd "$TF_DIR"

echo "==> This will DESTROY all CloudOptimizer resources for environment '${ENVIRONMENT}'."
echo "    This includes DynamoDB tables (all scan history + findings will be lost)."
read -r -p "Type the environment name ('${ENVIRONMENT}') to confirm: " confirm

if [ "$confirm" != "$ENVIRONMENT" ]; then
  echo "Confirmation did not match. Aborted."
  exit 1
fi

terraform destroy
