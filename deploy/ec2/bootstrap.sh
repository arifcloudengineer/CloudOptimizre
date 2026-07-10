#!/usr/bin/env bash
# CloudOptimizer EC2 bootstrap.
# Run this ON the EC2 instance (as root, or via `sudo`), after the repo has
# been uploaded to /opt/cloudoptimizer (see EC2-DEPLOY.md step 4).
#
# What this does:
#   1. Installs Python 3.12, Node 20, nginx
#   2. Creates a venv and installs backend/requirements.txt
#   3. Builds the frontend and serves it via nginx on port 80
#   4. Runs the FastAPI backend as a systemd service on 127.0.0.1:8000,
#      reverse-proxied by nginx under /api/
#   5. Installs a cron job that runs the scanner every night at 02:00 UTC
#      (replaces the EventBridge -> Lambda trigger used in the serverless build)
set -euo pipefail

APP_DIR="/opt/cloudoptimizer"
SERVICE_USER="cloudoptimizer"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root (sudo $0)"
  exit 1
fi

if [ ! -d "$APP_DIR" ]; then
  echo "Expected the repo at $APP_DIR — upload it first (see EC2-DEPLOY.md step 4)."
  exit 1
fi

echo "==> Installing system packages"
apt-get update -y
apt-get install -y python3.12 python3.12-venv python3-pip nginx curl git

if ! command -v node >/dev/null; then
  echo "==> Installing Node 20"
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi

echo "==> Creating service user"
id -u "$SERVICE_USER" &>/dev/null || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$SERVICE_USER"
chown -R "$SERVICE_USER":"$SERVICE_USER" "$APP_DIR"

echo "==> Setting up backend venv"
cd "$APP_DIR/backend"
sudo -u "$SERVICE_USER" python3.12 -m venv .venv
sudo -u "$SERVICE_USER" .venv/bin/pip install -q -r requirements.txt

echo "==> Building frontend"
cd "$APP_DIR/frontend"
npm install
npm run build
# nginx will serve frontend/dist directly

echo "==> Installing systemd service for the API"
cp "$APP_DIR/deploy/ec2/cloudoptimizer-api.service" /etc/systemd/system/cloudoptimizer-api.service
systemctl daemon-reload
systemctl enable cloudoptimizer-api
systemctl restart cloudoptimizer-api

echo "==> Configuring nginx"
cp "$APP_DIR/deploy/ec2/nginx-cloudoptimizer.conf" /etc/nginx/sites-available/cloudoptimizer
ln -sf /etc/nginx/sites-available/cloudoptimizer /etc/nginx/sites-enabled/cloudoptimizer
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

echo "==> Installing scanner cron job (daily 02:00 UTC)"
CRON_LINE="0 2 * * * $SERVICE_USER cd $APP_DIR/backend && $APP_DIR/backend/.venv/bin/python $APP_DIR/deploy/ec2/run_scan.py >> /var/log/cloudoptimizer-scan.log 2>&1"
grep -qF "$APP_DIR/deploy/ec2/run_scan.py" /etc/crontab || echo "$CRON_LINE" >> /etc/crontab

echo "==> Done."
echo "    API health check:  curl http://localhost/api/health"
echo "    Dashboard:         http://<instance-public-ip>/"
echo "    Trigger a scan now: sudo -u $SERVICE_USER $APP_DIR/backend/.venv/bin/python $APP_DIR/deploy/ec2/run_scan.py"
