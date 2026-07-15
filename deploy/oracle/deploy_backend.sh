#!/usr/bin/env bash
#
# deploy_backend.sh — install/update the BankongSeton API + web dashboard on the
# Oracle VM, alongside hostbox. Idempotent.
#
# Installs the systemd units (api + web only — kiosk/tech are on-prem RFID and
# are NOT deployed to this cloud box) and an nginx vhost, then starts them.
# Requires /opt/bankongseton (code) + /opt/bankongseton/.env (DATABASE_URL etc.).
#
# Run as root:  sudo bash deploy_backend.sh
set -euo pipefail

APP_DIR=/opt/bankongseton
DEPLOY_DIR="$APP_DIR/deploy/oracle"
USER_NAME=ubuntu
DOMAIN="${DOMAIN:-bankongseton.local}"   # set to your backend domain (named vhost)
NGINX_SITE=/etc/nginx/sites-available/bankongseton

[ -f "$APP_DIR/.env" ] || { echo "ABORT: $APP_DIR/.env missing (need DATABASE_URL etc.)"; exit 1; }

echo "==> Installing BankongSeton backend (api + web) -> $DOMAIN"

# ── systemd units (drop __APP_DIR__/__USER__ placeholders) ──
sudo sed "s#__APP_DIR__#$APP_DIR#g; s#__USER__#$USER_NAME#g" \
  "$DEPLOY_DIR/bankongseton-api.service"  > /etc/systemd/system/bankongseton-api.service
sudo sed "s#__APP_DIR__#$APP_DIR#g; s#__USER__#$USER_NAME#g" \
  "$DEPLOY_DIR/bankongseton-web.service"  > /etc/systemd/system/bankongseton-web.service
sudo systemctl daemon-reload
sudo systemctl enable bankongseton-api bankongseton-web

# ── nginx vhost (named server_name so it coexists with hostbox's default_server) ──
sudo tee "$NGINX_SITE" >/dev/null <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;
    client_max_body_size 10M;

    # API: /api/* -> gunicorn on 5001
    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }

    # Dashboard (admin/finance/cashier POS + SocketIO) -> gunicorn on 5000
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }
}
EOF
sudo ln -sf "$NGINX_SITE" /etc/nginx/sites-enabled/bankongseton
sudo nginx -t
sudo systemctl reload nginx

echo "==> Starting services"
sudo systemctl restart bankongseton-api bankongseton-web
sleep 3
sudo systemctl status bankongseton-api bankongseton-web --no-pager | grep -E "Active:|loaded|failed" || true
echo "==> API health:"; curl -sk https://localhost/api/health || echo "(not up — check journalctl -u bankongseton-api)"
echo "==> Web:";      curl -skI https://localhost/        | head -1 || echo "(not up — check journalctl -u bankongseton-web)"
