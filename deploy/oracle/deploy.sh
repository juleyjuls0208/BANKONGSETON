#!/usr/bin/env bash
#
# BANKONGSETON — redeploy after a code change.
# Run on the VM:  sudo bash /opt/bankongseton/deploy/oracle/deploy.sh
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/bankongseton}"
DEPLOY_DIR="$APP_DIR/deploy/oracle"
USER_NAME="banko"

echo "==> Pulling latest"
sudo -u "$USER_NAME" git -C "$APP_DIR" pull --ff-only || true

echo "==> Installing python deps"
sudo -u "$USER_NAME" bash -c "
  source '$APP_DIR/venv/bin/activate'
  pip install -r '$APP_DIR/backend/api/requirements_api.txt'
  pip install -r '$APP_DIR/backend/dashboard/requirements.txt'
  pip install -r '$DEPLOY_DIR/requirements-deploy.txt'
"

echo "==> Restarting services"
sudo systemctl restart bankongseton-api bankongseton-web bankongseton-kiosk bankongseton-tech
sleep 2
sudo systemctl status bankongseton-api bankongseton-web bankongseton-kiosk bankongseton-tech --no-pager
echo "==> API health:"
curl -sk https://localhost/api/health || echo "(API not reachable — check journalctl -u bankongseton-api)"
echo "==> Kiosk health:"
curl -sk https://localhost/kiosk/api/kiosk/health || echo "(Kiosk not reachable — check journalctl -u bankongseton-kiosk)"
echo "==> Tech health:"
curl -sk https://localhost/tech/api/tech/health || echo "(Tech not reachable — check journalctl -u bankongseton-tech)"
