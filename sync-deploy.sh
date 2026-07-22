#!/usr/bin/env bash
# sync-deploy.sh — push local backend+deploy to the live Oracle VM and restart
# the web dashboard. Run from repo root:  bash sync-deploy.sh
# The VM /opt/bankongseton is a non-git copy (tar sync), web runs `python web_app.py`
# under systemd.  ponytail: ships whole backend+deploy trees each time; switch to
# rsync if it ever gets slow.
set -euo pipefail

KEY="/c/Users/admin/Downloads/server keys/ssh-key-2026-06-19.key"
HOST="ubuntu@149.118.60.251"
APP=/opt/bankongseton
SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=no "$HOST")
URL="https://bankongseton.149-118-60-251.sslip.io"

cd "$(dirname "$0")"

echo "==> syncing backend + deploy"
tar czf - backend deploy | "${SSH[@]}" "sudo tar xzf - -C $APP"

echo "==> restarting web dashboard"
"${SSH[@]}" "sudo systemctl restart bankongseton-web"
sleep 2
"${SSH[@]}" "sudo systemctl is-active bankongseton-web"

echo "==> health"
curl -sk "$URL/api/health" || echo "(api not reachable — check journalctl -u bankongseton-web)"
