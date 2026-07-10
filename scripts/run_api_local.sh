#!/usr/bin/env bash
# Runs the FastAPI backend locally against real (or LocalStack) AWS DynamoDB.
# Requires AWS credentials in the environment/profile with read access to the
# CloudOptimizer DynamoDB tables.
set -euo pipefail

cd "$(dirname "$0")/../backend"

if [ ! -d ".venv" ]; then
  echo "==> Creating virtualenv"
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt

export RESOURCES_TABLE="${RESOURCES_TABLE:-cloudoptimizer-resources-dev}"
export SCAN_HISTORY_TABLE="${SCAN_HISTORY_TABLE:-cloudoptimizer-resources-dev-scan-history}"
export SCANNER_LAMBDA_NAME="${SCANNER_LAMBDA_NAME:-cloudoptimizer-scanner-dev}"

echo "==> Starting API on http://localhost:8000 (docs at /docs)"
uvicorn api.main:app --reload --port 8000
