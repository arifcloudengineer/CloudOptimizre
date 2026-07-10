"""
Lambda entry point for the FastAPI app, via Mangum.

Deploy this behind an API Gateway HTTP API or a Lambda Function URL:
  handler = "api.lambda_handler.handler"

Locally, run api/main.py directly with uvicorn instead (see scripts/run_api_local.sh)
-- Mangum is only needed for the Lambda deployment path.
"""
from mangum import Mangum
from api.main import app

handler = Mangum(app)
