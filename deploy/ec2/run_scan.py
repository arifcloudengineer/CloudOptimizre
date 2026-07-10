#!/usr/bin/env python3
"""
Cron entry point for CloudOptimizer's scanner on EC2 (no Lambda involved).
Runs the exact same scan/persist/alert logic as backend/lambda_handler.py,
just invoked directly instead of via a Lambda event.

Usage (see deploy/ec2/bootstrap.sh for the crontab line that calls this):
    cd /opt/cloudoptimizer/backend && /opt/cloudoptimizer/backend/.venv/bin/python \
        /opt/cloudoptimizer/deploy/ec2/run_scan.py
"""
import os
import sys

# backend/ must be importable -- add it to sys.path in case this is invoked
# from outside that directory (e.g. by cron with an unusual working dir).
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
sys.path.insert(0, os.path.abspath(BACKEND_DIR))

from lambda_handler import handler  # noqa: E402

if __name__ == "__main__":
    result = handler(event={}, context=None)
    print(result["body"])
