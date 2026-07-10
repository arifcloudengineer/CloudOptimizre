#!/usr/bin/env bash
# Deploys CloudOptimizer infrastructure to AWS.
# Prerequisites: terraform >= 1.5, aws CLI configured with credentials that
# can create IAM roles/policies, Lambda, DynamoDB, SNS, S3, EventBridge.
set -euo pipefail

ENVIRONMENT="${1:-dev}"
TF_DIR="terraform/environments/${ENVIRONMENT}"

if [ ! -d "$TF_DIR" ]; then
  echo "No environment '${ENVIRONMENT}' found under terraform/environments/"
  exit 1
fi

echo "==> Deploying CloudOptimizer (${ENVIRONMENT})"

cd "$TF_DIR"

if [ ! -f terraform.tfvars ]; then
  echo "!! terraform.tfvars not found. Copy terraform.tfvars.example -> terraform.tfvars and fill in your values first."
  exit 1
fi

echo "==> terraform init"
terraform init

echo "==> terraform plan"
terraform plan -out=tfplan

read -r -p "Apply this plan? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "Aborted."
  exit 0
fi

echo "==> terraform apply"
terraform apply tfplan

echo "==> Done. Outputs:"
terraform output

cat <<EOF

Next steps:
1. Run the backend locally (see root README "Run locally") or deploy the
   FastAPI app behind API Gateway/Lambda Function URL/ECS -- Terraform for
   the API layer itself is intentionally left for you to add (this project
   ships the scanner infra; the API can run anywhere that reaches DynamoDB).
2. Trigger a first scan:
     aws lambda invoke --function-name cloudoptimizer-scanner-${ENVIRONMENT} \\
       --payload '{}' --cli-binary-format raw-in-base64-out /tmp/out.json && cat /tmp/out.json
3. Point the frontend's VITE_API_BASE_URL at wherever you run the API.
EOF
